package com.stokuj.books.author;

public record AuthorResponse(
        Long id,
        String name,
        String bio,
        String avatarUrl,
        java.time.LocalDate birthDate
) {}
