package com.stokuj.books.book;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class AdminBookForm {

    private String title;
    private String author;
    private Integer year;
    private String isbn;
    private String description;
    private Integer pageCount;
    private String genres;
    private String tags;
}
