package com.stokuj.books.book.book.dto;

import java.util.List;
import java.util.Set;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

@Getter
@Setter
public class BookPatchRequest {

    @Size(max = 255, message = "Title is too long")
    private String title;

    @Size(max = 255, message = "Author name is too long")
    private String author;

    @Min(value = 0, message = "Year must be positive")
    private Integer year;

    private String isbn;
    private String description;

    @Min(value = 0, message = "Page count must be positive")
    private Integer pageCount;

    private Set<String> genres;
    private List<String> tags;
}
