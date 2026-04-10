package com.stokuj.books.book.character;

public record CharacterRelationResponse(
        Long id,
        String sourceCharacterName,
        String targetCharacterName,
        String relation,
        String evidence,
        double confidence
) {}
