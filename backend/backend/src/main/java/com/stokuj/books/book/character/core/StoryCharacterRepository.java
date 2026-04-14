package com.stokuj.books.book.character.core;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface StoryCharacterRepository extends JpaRepository<StoryCharacter, Long> {
    Optional<StoryCharacter> findByNameIgnoreCase(String name);
}
