package com.stokuj.books.integration.processor;

import com.stokuj.books.integration.dto.BookFindPairsResult;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.character.relation.StoryCharacterRelation;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import com.stokuj.books.book.character.core.StoryCharacterService;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import com.stokuj.books.book.character.core.StoryCharacter;

import java.util.List;
import java.util.Map;
import java.util.Objects;

@Component
public class RelationsResultProcessor {

    private final StoryCharacterRelationRepository characterRelationRepository;
    private final StoryCharacterService characterService;
    private final ChapterEventProducer chapterEventProducer;

    public RelationsResultProcessor(StoryCharacterRelationRepository characterRelationRepository,
                                    StoryCharacterService characterService,
                                    ChapterEventProducer chapterEventProducer) {
        this.characterRelationRepository = characterRelationRepository;
        this.characterService = characterService;
        this.chapterEventProducer = chapterEventProducer;
    }

    @Transactional
    public void processFindPairsResult(Book book, BookFindPairsResult result) {
        if (result.pairs() != null) {
            result.pairs().forEach(pairResult -> {
                List<String> pair = pairResult.pair();
                if (pair == null || pair.size() < 2) {
                    return;
                }
                String sourceName = normalizeName(pair.get(0));
                String targetName = normalizeName(pair.get(1));
                if (sourceName == null || targetName == null) {
                    return;
                }
                StoryCharacter source = characterService.findOrCreate(sourceName);
                StoryCharacter target = characterService.findOrCreate(targetName);
                StoryCharacterRelation relation = characterRelationRepository
                        .findByBookIdAndSourceIdAndTargetId(book.getId(), source.getId(), target.getId())
                        .orElse(null);
                if (relation == null) {
                    relation = new StoryCharacterRelation();
                    relation.setBook(book);
                    relation.setSource(source);
                    relation.setTarget(target);
                    characterRelationRepository.save(relation);
                }
            });
        }

        if (result.pairs() != null && !result.pairs().isEmpty()) {
            chapterEventProducer.sendBookForRelations(book.getId(), result.pairs());
        }
    }

    @Transactional
    public void processRelationsResult(Book book, Map<String, Object> result) {
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
                                    StoryCharacter source = characterService.findOrCreate(sourceName);
                                    StoryCharacter target = characterService.findOrCreate(targetName);
                                    StoryCharacterRelation relation = characterRelationRepository
                                            .findByBookIdAndSourceIdAndTargetId(book.getId(), source.getId(), target.getId())
                                            .orElseGet(() -> {
                                                StoryCharacterRelation created = new StoryCharacterRelation();
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
