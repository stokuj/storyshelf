package com.stokuj.books.book;

public record CharacterRelationResponse(
        Long id,
        String sourceCharacterName,
        String targetCharacterName,
        String relation,
        String evidence,
        double confidence
) {}
