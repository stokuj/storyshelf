package com.stokuj.books.repository;

import com.stokuj.books.model.entity.BookCharacter;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookCharacterRepository extends JpaRepository<BookCharacter, Long> {
    Optional<BookCharacter> findByBookIdAndCharacterId(Long bookId, Long characterId);

    List<BookCharacter> findAllByBookId(Long bookId);

    void deleteAllByBookId(Long bookId);
}
