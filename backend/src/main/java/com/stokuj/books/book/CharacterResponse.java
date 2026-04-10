package com.stokuj.books.book;

public record CharacterResponse(
        Long id,
        String name,
        int mentionCount,
        String role
) {}
