package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Character;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CharacterRepository extends JpaRepository<Character, Long> {
    Optional<Character> findByNameIgnoreCase(String name);
}
