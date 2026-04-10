package com.stokuj.books.book;

import com.stokuj.books.book.Character;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CharacterRepository extends JpaRepository<Character, Long> {
    Optional<Character> findByNameIgnoreCase(String name);
}
