package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.StoryCharacter;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookCharacterRepository extends JpaRepository<StoryCharacter, Long> {
    Optional<StoryCharacter> findByBookIdAndCharacterId(Long bookId, Long characterId);

    List<StoryCharacter> findAllByBookId(Long bookId);

    @org.springframework.data.jpa.repository.Query("SELECT bc FROM StoryCharacter bc JOIN FETCH bc.character WHERE bc.book.id = :bookId")
    List<StoryCharacter> findAllByBookIdWithCharacter(@org.springframework.data.repository.query.Param("bookId") Long bookId);

    void deleteAllByBookId(Long bookId);
}
