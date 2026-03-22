package com.stokuj.books.dto;

import jakarta.validation.constraints.*;
import java.util.List;
import java.util.Set;

public class BookRequest {

    @NotBlank(message = "Tytuł nie może być pusty")
    private String title;

    @NotBlank(message = "Autor nie może być pusty")
    private String author;

    @Min(value = 1, message = "Rok musi być większy niż 0")
    private int year;

    @Pattern(regexp = "^(97(8|9))?\\d{9}(\\d|X)$", message = "Nieprawidłowy format ISBN")
    private String isbn;

    @Size(max = 2000, message = "Opis nie może przekraczać 2000 znaków")
    private String description;

    @Min(value = 1, message = "Liczba stron musi być większa niż 0")
    private int pageCount;

    // === KATEGORYZACJA ===
    private Set<String> genres;
    private List<String> tags;

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getAuthor() { return author; }
    public void setAuthor(String author) { this.author = author; }

    public int getYear() { return year; }
    public void setYear(int year) { this.year = year; }

    public String getIsbn() { return isbn; }
    public void setIsbn(String isbn) { this.isbn = isbn; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getPageCount() { return pageCount; }
    public void setPageCount(int pageCount) { this.pageCount = pageCount; }

    public Set<String> getGenres() { return genres; }
    public void setGenres(Set<String> genres) { this.genres = genres; }

    public List<String> getTags() { return tags; }
    public void setTags(List<String> tags) { this.tags = tags; }
}