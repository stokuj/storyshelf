package com.stokuj.books.author.dto;

public record AuthorResponse(
        Long id,
        String name,
        String bio,
        String avatarUrl,
        java.time.LocalDate birthDate
) {}
