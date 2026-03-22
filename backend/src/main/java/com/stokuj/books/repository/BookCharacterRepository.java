package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.BookCharacter;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookCharacterRepository extends JpaRepository<BookCharacter, Long> {
}
