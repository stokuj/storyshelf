package com.stokuj.books.book.book.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.HashSet;
import java.util.Set;

public record BookRequest(
        @NotBlank(message = "Title is required")
        String title,

        @NotNull(message = "Author is required")
        Long authorId,

        @Min(value = 1, message = "Year must be a positive number")
        int year,

        String isbn,
        String description,

        @Min(value = 1, message = "Page count must be positive")
        int pageCount,

        Set<String> genres,

        Set<Long> tagIds
) {
    public BookRequest {
        if (genres == null) {
            genres = new HashSet<>();
        }
        if (tagIds == null) {
            tagIds = new HashSet<>();
        }
    }
}
