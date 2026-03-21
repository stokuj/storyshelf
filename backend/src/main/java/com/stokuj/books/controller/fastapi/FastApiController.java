package com.stokuj.books.controller.fastapi;

import com.stokuj.books.dto.fastapi.AnalyseResponse;
import com.stokuj.books.dto.fastapi.BookFindPairsResult;
import com.stokuj.books.model.entity.Book;
import com.stokuj.books.model.entity.BookChapter;
import com.stokuj.books.model.entity.BookCharacter;
import com.stokuj.books.model.entity.Character;
import com.stokuj.books.model.entity.CharacterRelation;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import com.stokuj.books.model.fastapi.NerResult;
import com.stokuj.books.service.CharacterService;
import com.stokuj.books.service.ChapterEventProducer;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/fastAPI")
public class FastApiController {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final CharacterService characterService;
    private final ChapterEventProducer chapterEventProducer;

    public FastApiController(BookChapterRepository chapterRepository,
                             BookRepository bookRepository,
                             BookCharacterRepository bookCharacterRepository,
                             CharacterRelationRepository characterRelationRepository,
                             CharacterService characterService,
                             ChapterEventProducer chapterEventProducer) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
        this.characterService = characterService;
        this.chapterEventProducer = chapterEventProducer;
    }

    @PatchMapping("/chapters/{chapterId}/analyse-result")
    public ResponseEntity<Void> updateAnalyseResult(@PathVariable Long chapterId,
                                                    @RequestBody AnalyseResponse result) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapter.setCharCount(result.analysis().charCount());
        chapter.setCharCountClean(result.analysis().charCountClean());
        chapter.setWordCount(result.analysis().wordCount());
        chapter.setTokenCount(result.analysis().tokenCount());
        chapter.setAnalysisCompleted(true);

        chapterRepository.save(chapter);

        return ResponseEntity.ok().build();
    }

    @PatchMapping("/chapters/{chapterId}/ner-result")
    @Transactional
    public ResponseEntity<Void> updateNerResult(@PathVariable Long chapterId,
                                                @RequestBody NerResult result) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapter.setNerResult(result);
        chapterRepository.save(chapter);

        Book book = bookRepository.findByIdForUpdate(chapter.getBook().getId()).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }
        if (result.getCharacters() != null) {
            result.getCharacters().forEach((name, count) -> {
                String normalized = normalizeName(name);
                if (normalized == null) {
                    return;
                }
                Character character = characterService.findOrCreate(normalized);
                BookCharacter bookCharacter = bookCharacterRepository
                        .findByBookIdAndCharacterId(book.getId(), character.getId())
                        .orElse(null);
                int increment = count != null ? count : 0;
                if (bookCharacter == null) {
                    bookCharacter = new BookCharacter();
                    bookCharacter.setBook(book);
                    bookCharacter.setCharacter(character);
                    bookCharacter.setMentionCount(increment);
                } else {
                    bookCharacter.setMentionCount(bookCharacter.getMentionCount() + increment);
                }
                bookCharacterRepository.save(bookCharacter);
            });
        }
        book.setNerCompletedCount(book.getNerCompletedCount() + 1);
        bookRepository.save(book);

        boolean readyForFindPairs = book.getNerCompletedCount() >= book.getChaptersCount();
        if (!readyForFindPairs && chapter.getChapterNumber() == 1) {
            readyForFindPairs = true;
        }

        if (readyForFindPairs && !characterRelationRepository.existsByBookId(book.getId())) {
            Map<String, Integer> characterMap = toCharacterMap(book.getId());
            if (characterMap.isEmpty()) {
                return ResponseEntity.ok().build();
            }
            List<BookChapter> chapters = chapterRepository.findAllByBookIdOrderByChapterNumber(book.getId());
            String fullContent = chapters.stream()
                    .map(BookChapter::getContent)
                    .collect(Collectors.joining("\n\n"));
            chapterEventProducer.sendBookForFindPairs(book.getId(), fullContent, characterMap);
        }

        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/find-pairs-result")
    public ResponseEntity<Void> updateBookFindPairsResult(@PathVariable Long bookId,
                                                          @RequestBody BookFindPairsResult result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        if (result.getPairs() != null) {
            result.getPairs().forEach(pairResult -> {
                List<String> pair = pairResult.getPair();
                if (pair == null || pair.size() < 2) {
                    return;
                }
                String sourceName = normalizeName(pair.get(0));
                String targetName = normalizeName(pair.get(1));
                if (sourceName == null || targetName == null) {
                    return;
                }
                Character source = characterService.findOrCreate(sourceName);
                Character target = characterService.findOrCreate(targetName);
                CharacterRelation relation = characterRelationRepository
                        .findByBookIdAndSourceIdAndTargetId(bookId, source.getId(), target.getId())
                        .orElse(null);
                if (relation == null) {
                    relation = new CharacterRelation();
                    relation.setBook(book);
                    relation.setSource(source);
                    relation.setTarget(target);
                    characterRelationRepository.save(relation);
                }
            });
        }

        if (result.getPairs() != null && !result.getPairs().isEmpty()) {
            chapterEventProducer.sendBookForRelations(bookId, result.getPairs());
        }

        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/relations-result")
    public ResponseEntity<Void> updateBookRelationsResult(@PathVariable Long bookId,
                                                          @RequestBody Map<String, Object> result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        Object allRelations = result.get("all_relations");
        if (allRelations instanceof List<?> relationsList) {
            relationsList.stream()
                    .filter(item -> item instanceof Map<?, ?>)
                    .map(item -> (Map<?, ?>) item)
                    .forEach(item -> {
                        Object relationsObj = item.get("relations");
                        if (!(relationsObj instanceof Map<?, ?> relationsMap)) {
                            return;
                        }
                        Object innerRelations = relationsMap.get("relations");
                        if (!(innerRelations instanceof List<?> innerList)) {
                            return;
                        }
                        innerList.stream()
                                .filter(rel -> rel instanceof Map<?, ?>)
                                .map(rel -> (Map<?, ?>) rel)
                                .forEach(rel -> {
                                    String sourceName = normalizeName(asString(rel.get("source")));
                                    String targetName = normalizeName(asString(rel.get("target")));
                                    if (sourceName == null || targetName == null) {
                                        return;
                                    }
                                    Character source = characterService.findOrCreate(sourceName);
                                    Character target = characterService.findOrCreate(targetName);
                                    CharacterRelation relation = characterRelationRepository
                                            .findByBookIdAndSourceIdAndTargetId(bookId, source.getId(), target.getId())
                                            .orElseGet(() -> {
                                                CharacterRelation created = new CharacterRelation();
                                                created.setBook(book);
                                                created.setSource(source);
                                                created.setTarget(target);
                                                return created;
                                            });
                                    relation.setRelation(blankToNull(asString(rel.get("relation"))));
                                    relation.setEvidence(blankToNull(asString(rel.get("evidence"))));
                                    relation.setConfidence(asDouble(rel.get("confidence")));
                                    characterRelationRepository.save(relation);
                                });
                    });
        }

        return ResponseEntity.ok().build();
    }

    @PostMapping("/chapters/{chapterId}/analyse")
    public ResponseEntity<Map<String, Object>> analyseChapter(@PathVariable Long chapterId) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapterEventProducer.sendChapterForAnalysis(chapter.getId(), chapter.getContent());
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "analysis_started", true
        ));
    }

    @PostMapping("/chapters/{chapterId}/ner")
    public ResponseEntity<Map<String, Object>> nerChapter(@PathVariable Long chapterId) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapterEventProducer.sendChapterForNer(chapter.getId(), chapter.getContent());
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "ner_started", true
        ));
    }

    private Map<String, Integer> toCharacterMap(Long bookId) {
        Map<String, Integer> map = new HashMap<>();
        bookCharacterRepository.findAllByBookId(bookId)
                .forEach(entry -> map.merge(entry.getCharacter().getName(),
                        entry.getMentionCount(), Integer::sum));
        return map;
    }

    private String normalizeName(String name) {
        if (name == null) {
            return null;
        }
        String normalized = name.trim();
        return normalized.isEmpty() ? null : normalized;
    }

    private String asString(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof String text) {
            return text;
        }
        return Objects.toString(value, null);
    }

    private String blankToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private Double asDouble(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value instanceof String text) {
            String trimmed = text.trim();
            if (trimmed.isEmpty()) {
                return null;
            }
            try {
                return Double.parseDouble(trimmed);
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

}
