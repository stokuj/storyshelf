package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.StoryCharacterRelation;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRelationRepository extends JpaRepository<StoryCharacterRelation, Long> {
    Optional<StoryCharacterRelation> findByBookIdAndSourceIdAndTargetId(Long bookId, Long sourceId, Long targetId);

    List<StoryCharacterRelation> findAllByBookId(Long bookId);

    boolean existsByBookId(Long bookId);

    void deleteAllByBookId(Long bookId);
}
