package com.stokuj.books.book;

import com.stokuj.books.book.BookCharacter;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface BookCharacterRepository extends JpaRepository<BookCharacter, Long> {
    Optional<BookCharacter> findByBookIdAndCharacterId(Long bookId, Long characterId);
    List<BookCharacter> findAllByBookId(Long bookId);
    void deleteAllByBookId(Long bookId);
    @Query("SELECT bc FROM BookCharacter bc JOIN FETCH bc.character WHERE bc.book.id = :bookId")
    List<BookCharacter> findAllByBookIdWithCharacter(Long bookId);

}
