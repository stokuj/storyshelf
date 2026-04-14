package com.stokuj.books.review.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ReviewRequest(
        @Min(value = 1, message = "Rating must be at least 1")
        @Max(value = 5, message = "Rating must not exceed 5")
        int rating,

        @NotBlank(message = "Review content cannot be empty")
        @Size(min = 10, max = 2000, message = "Review must be between 10 and 2000 characters long")
        String content
) {}