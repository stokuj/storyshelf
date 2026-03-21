package com.stokuj.books.repository;

import com.stokuj.books.model.entity.Character;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRepository extends JpaRepository<Character, Long> {
    Optional<Character> findByNameIgnoreCase(String name);
}
