package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.StoryCharacter;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRepository extends JpaRepository<StoryCharacter, Long> {
    Optional<StoryCharacter> findByNameIgnoreCase(String name);
}
