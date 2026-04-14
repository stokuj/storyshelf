package com.stokuj.books.book.book.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import java.util.List;
import java.util.Set;

public record BookPatchRequest(
    @Size(max = 255, message = "Title is too long")
    String title,

    @Size(max = 255, message = "Author name is too long")
    String author,

    @Min(value = 0, message = "Year must be positive")
    Integer year,

    String isbn,
    String description,

    @Min(value = 0, message = "Page count must be positive")
    Integer pageCount,

    Set<String> genres,
    List<String> tags
) {}
