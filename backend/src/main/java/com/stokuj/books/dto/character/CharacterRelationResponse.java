package com.stokuj.books.dto.character;

public record CharacterRelationResponse(
        Long id,
        String sourceCharacterName,
        String targetCharacterName,
        String relation,
        String evidence,
        double confidence
) {}