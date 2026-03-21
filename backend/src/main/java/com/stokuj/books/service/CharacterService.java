package com.stokuj.books.service;

import com.stokuj.books.model.entity.Character;
import com.stokuj.books.repository.CharacterRepository;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CharacterService {

    private final CharacterRepository characterRepository;

    public CharacterService(CharacterRepository characterRepository) {
        this.characterRepository = characterRepository;
    }

    @Transactional
    public Character findOrCreate(String name) {
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
                        Character character = new Character();
                        character.setName(normalized);
                        return characterRepository.saveAndFlush(character);
                    } catch (DataIntegrityViolationException e) {
                        return characterRepository.findByNameIgnoreCase(normalized)
                                .orElseThrow();
                    }
                });
    }
}
