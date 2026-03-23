package com.stokuj.books.dto.review;

import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Getter
@Setter
public class ReviewRequest {

    @Min(value = 1, message = "Rating must be at least 1")
    @Max(value = 5, message = "Rating must not exceed 5")
    private int rating;

    @NotBlank(message = "Review content cannot be empty")
    @Size(max = 2000, message = "Review is too long")
    private String content;
}
