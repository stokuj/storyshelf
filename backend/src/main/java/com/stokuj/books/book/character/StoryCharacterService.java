package com.stokuj.books.book.character;

import com.stokuj.books.book.character.StoryCharacterRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;
import com.stokuj.books.book.character.StoryCharacter;

@Service
public class StoryCharacterService {

    private final StoryCharacterRepository characterRepository;

    public StoryCharacterService(StoryCharacterRepository characterRepository) {
        this.characterRepository = characterRepository;
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public StoryCharacter findOrCreate(String name) {
        if (name == null) {
            throw new IllegalArgumentException("Character name cannot be null");
        }
        String normalized = name.trim();
        if (normalized.isEmpty()) {
            throw new IllegalArgumentException("Character name cannot be blank");
        }

        return characterRepository.findByNameIgnoreCase(normalized)
                .orElseGet(() -> {
                    try {
                        StoryCharacter character = new StoryCharacter();
                        character.setName(normalized);
                        return characterRepository.saveAndFlush(character);
                    } catch (DataIntegrityViolationException e) {
                        return characterRepository.findByNameIgnoreCase(normalized)
                                .orElseThrow();
                    }
                });
    }
}
