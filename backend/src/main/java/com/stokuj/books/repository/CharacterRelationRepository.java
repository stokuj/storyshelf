package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.CharacterRelation;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface CharacterRelationRepository extends JpaRepository<CharacterRelation, Long> {
    boolean existsByBookId(Long bookId);
    Optional<CharacterRelation> findByBookIdAndSourceIdAndTargetId(Long bookId, Long sourceId, Long targetId);
    List<CharacterRelation> findAllByBookId(Long bookId);
    void deleteAllByBookId(Long bookId);
}
