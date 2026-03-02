package com.stokuj.books.dto;

import lombok.Data;

@Data
public class BookRequest {
    private String title;
    private String author;
    private int year;
}