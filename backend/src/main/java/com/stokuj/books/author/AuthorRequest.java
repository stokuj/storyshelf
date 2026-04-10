package com.stokuj.books.author;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record AuthorRequest(
        @NotBlank(message = "Author name is required")
        @Size(max = 255, message = "Name cannot exceed 255 characters")
        String name,

        String bio,
        LocalDate birthDate
) {}
