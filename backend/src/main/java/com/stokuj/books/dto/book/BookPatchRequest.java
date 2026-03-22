package com.stokuj.books.dto.book;

import java.util.List;
import java.util.Set;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class BookPatchRequest {

    private String title;
    private String author;
    private Integer year;
    private String isbn;
    private String description;
    private Integer pageCount;
    private Set<String> genres;
    private List<String> tags;
}
