package com.stokuj.books.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public class ReviewRequest {

    @NotNull(message = "Ocena jest wymagana")
    @Min(value = 1, message = "Ocena musi być z zakresu 1-5")
    @Max(value = 5, message = "Ocena musi być z zakresu 1-5")
    private Integer rating;

    @Size(max = 2000, message = "Recenzja nie może przekraczać 2000 znaków")
    private String content;

    public Integer getRating() {
        return rating;
    }

    public void setRating(Integer rating) {
        this.rating = rating;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }
}
