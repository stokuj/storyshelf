package com.stokuj.books.dto.character;

public record CharacterResponse(
        Long id,
        String name,
        int mentionCount,
        String role
) {}