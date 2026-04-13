package com.stokuj.books.book.character.relation.dto;

public record CharacterRelationResponse(
        Long id,
        String sourceCharacterName,
        String targetCharacterName,
        String relation,
        String evidence,
        double confidence
) {}
