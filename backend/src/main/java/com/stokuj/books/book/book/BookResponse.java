package com.stokuj.books.book.book;

import java.util.List;
import java.util.Set;

public record BookResponse(
        Long id,
        String title,
        String author,
        int year,
        String isbn,
        String description,
        int pageCount,
        Set<String> genres,
        List<String> tags,
        double rating,
        int ratingsCount
) {}
