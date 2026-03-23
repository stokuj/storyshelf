package com.stokuj.books.dto.book;

import java.util.List;
import java.util.Set;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Min;

@Getter
@Setter
public class BookRequest {

    @NotBlank(message = "Title is required")
    private String title;

    @NotBlank(message = "Author is required")
    private String author;

    @Min(value = 0, message = "Year must be positive")
    private int year;

    private String isbn;
    private String description;

    @Min(value = 0, message = "Page count must be positive")
    private int pageCount;

    private Set<String> genres;
    private List<String> tags;
}
