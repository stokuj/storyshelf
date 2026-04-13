package com.stokuj.books.book.character.core.dto;

public record CharacterResponse(
        Long id,
        String name,
        int mentionCount,
        String role
) {}
