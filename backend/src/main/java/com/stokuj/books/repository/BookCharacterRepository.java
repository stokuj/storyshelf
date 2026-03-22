package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.BookStoryCharacters;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookCharacterRepository extends JpaRepository<BookStoryCharacters, Long> {
    Optional<BookStoryCharacters> findByBookIdAndCharacterId(Long bookId, Long characterId);

    List<BookStoryCharacters> findAllByBookId(Long bookId);

    @org.springframework.data.jpa.repository.Query("SELECT bc FROM BookStoryCharacters bc JOIN FETCH bc.character WHERE bc.book.id = :bookId")
    List<BookStoryCharacters> findAllByBookIdWithCharacter(@org.springframework.data.repository.query.Param("bookId") Long bookId);

    void deleteAllByBookId(Long bookId);
}
