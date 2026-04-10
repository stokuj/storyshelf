package com.stokuj.books.book.character;

import com.stokuj.books.book.character.StoryCharacterRelation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface StoryCharacterRelationRepository extends JpaRepository<StoryCharacterRelation, Long> {
    boolean existsByBookId(Long bookId);
    Optional<StoryCharacterRelation> findByBookIdAndSourceIdAndTargetId(Long bookId, Long sourceId, Long targetId);
    List<StoryCharacterRelation> findAllByBookId(Long bookId);
    void deleteAllByBookId(Long bookId);
}
