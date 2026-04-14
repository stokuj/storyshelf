package com.stokuj.books.author.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record AuthorRequest(
        @NotBlank(message = "Author name is required")
        @Size(min = 3, max = 80, message = "Name must be between 6 and 80 characters long")
        String name,

        @Size(min = 10, max = 160, message = "Name must be between 10 and 160 characters long")
        String bio,
        LocalDate birthDate
) {}
