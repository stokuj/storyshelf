package com.stokuj.books.service;

import com.stokuj.books.model.entity.Book;
import com.stokuj.books.model.entity.BookChapter;
import com.stokuj.books.model.entity.BookCharacter;
import com.stokuj.books.model.entity.Character;
import com.stokuj.books.model.fastapi.NerResult;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Component
public class NerResultProcessor {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final CharacterService characterService;
    private final ChapterEventProducer chapterEventProducer;

    public NerResultProcessor(BookChapterRepository chapterRepository,
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

    @Transactional
    public void process(BookChapter chapter, NerResult result) {
        chapter.setNerResult(result);
        chapterRepository.save(chapter);

        Book book = bookRepository.findByIdForUpdate(chapter.getBook().getId()).orElse(null);
        if (book == null) {
            return;
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
                return;
            }
            List<BookChapter> chapters = chapterRepository.findAllByBookIdOrderByChapterNumber(book.getId());
            String fullContent = chapters.stream()
                    .map(BookChapter::getContent)
                    .collect(Collectors.joining("\n\n"));
            chapterEventProducer.sendBookForFindPairs(book.getId(), fullContent, characterMap);
        }
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
}
