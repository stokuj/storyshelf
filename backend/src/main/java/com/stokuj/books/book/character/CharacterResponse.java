package com.stokuj.books.book.character;

public record CharacterResponse(
        Long id,
        String name,
        int mentionCount,
        String role
) {}
