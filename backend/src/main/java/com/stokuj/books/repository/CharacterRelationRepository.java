package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.CharacterRelation;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CharacterRelationRepository extends JpaRepository<CharacterRelation, Long> {
}
