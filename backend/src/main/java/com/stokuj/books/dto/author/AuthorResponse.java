package com.stokuj.books.dto.author;

public record AuthorResponse(
        Long id,
        String name,
        String bio,
        String avatarUrl,
        java.time.LocalDate birthDate
) {}