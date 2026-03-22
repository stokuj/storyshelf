package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Character;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRepository extends JpaRepository<Character, Long> {
}
