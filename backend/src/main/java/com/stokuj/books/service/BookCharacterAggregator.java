package com.stokuj.books.service;

import com.stokuj.books.dto.integration.NerResult;
import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.entity.BookCharacter;
import com.stokuj.books.domain.entity.Character;
import com.stokuj.books.repository.BookCharacterRepository;
import java.util.HashMap;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class BookCharacterAggregator {

    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterService characterService;

    public BookCharacterAggregator(BookCharacterRepository bookCharacterRepository,
                                   CharacterService characterService) {
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterService = characterService;
    }

    public void applyNerResult(Book book, NerResult result) {
        if (result.getCharacters() == null) {
            return;
        }
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
                bookCharacter.setRole(null);
                bookCharacter.setMentionCount(increment);
            } else {
                bookCharacter.setMentionCount(bookCharacter.getMentionCount() + increment);
            }
            bookCharacterRepository.save(bookCharacter);
        });
    }

    public Map<String, Integer> toCharacterMap(Long bookId) {
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
