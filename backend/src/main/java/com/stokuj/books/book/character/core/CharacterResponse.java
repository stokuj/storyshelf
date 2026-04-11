package com.stokuj.books.book.character.core;

public record CharacterResponse(
        Long id,
        String name,
        int mentionCount,
        String role
) {}
