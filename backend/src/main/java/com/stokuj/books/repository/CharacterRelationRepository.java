package com.stokuj.books.repository;

import com.stokuj.books.model.entity.CharacterRelation;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRelationRepository extends JpaRepository<CharacterRelation, Long> {
    Optional<CharacterRelation> findByBookIdAndSourceIdAndTargetId(Long bookId, Long sourceId, Long targetId);

    List<CharacterRelation> findAllByBookId(Long bookId);

    boolean existsByBookId(Long bookId);

    void deleteAllByBookId(Long bookId);
}
