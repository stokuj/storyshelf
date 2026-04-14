package com.stokuj.books.book.book.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import java.util.List;
import java.util.Set;

public record BookRequest(
    @NotBlank(message = "Title is required")
    String title,

    @NotBlank(message = "Author is required")
    String author,

    @Min(value = 0, message = "Year must be positive")
    int year,

    String isbn,
    String description,

    @Min(value = 0, message = "Page count must be positive")
    int pageCount,

    Set<String> genres,
    List<String> tags
) {}
