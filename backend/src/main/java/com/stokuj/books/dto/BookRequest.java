package com.stokuj.books.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;

public class BookRequest {

    @NotBlank(message = "Tytuł nie może być pusty")
    private String title;

    @NotBlank(message = "Autor nie może być pusty")
    private String author;

    @Min(value = 1, message = "Rok musi być większy niż 0")
    private int year;

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getAuthor() {
        return author;
    }

    public void setAuthor(String author) {
        this.author = author;
    }

    public int getYear() {
        return year;
    }

    public void setYear(int year) {
        this.year = year;
    }
}
