package com.stokuj.books.dto.request;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public class AdminBookForm {

    @NotBlank(message = "Tytuł nie może być pusty")
    private String title;

    @NotBlank(message = "Autor nie może być pusty")
    private String author;

    @NotNull(message = "Rok jest wymagany")
    @Min(value = 1, message = "Rok musi być większy niż 0")
    private Integer year;

    @Pattern(regexp = "^(97(8|9))?\\d{9}(\\d|X)$", message = "Nieprawidłowy format ISBN")
    private String isbn;

    @Size(max = 2000, message = "Opis nie może przekraczać 2000 znaków")
    private String description;

    @NotNull(message = "Liczba stron jest wymagana")
    @Min(value = 1, message = "Liczba stron musi być większa niż 0")
    private Integer pageCount;

    private String genres;
    private String tags;

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

    public Integer getYear() {
        return year;
    }

    public void setYear(Integer year) {
        this.year = year;
    }

    public String getIsbn() {
        return isbn;
    }

    public void setIsbn(String isbn) {
        this.isbn = isbn;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Integer getPageCount() {
        return pageCount;
    }

    public void setPageCount(Integer pageCount) {
        this.pageCount = pageCount;
    }

    public String getGenres() {
        return genres;
    }

    public void setGenres(String genres) {
        this.genres = genres;
    }

    public String getTags() {
        return tags;
    }

    public void setTags(String tags) {
        this.tags = tags;
    }
}
