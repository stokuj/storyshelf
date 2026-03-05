package com.stokuj.books.dto;

import com.stokuj.books.model.Book;
import com.stokuj.books.model.ReadingStatus;

import java.time.Instant;

public class UserBookResponse {

    private Book book;
    private ReadingStatus status;
    private Instant createdAt;

    public UserBookResponse(Book book, ReadingStatus status, Instant createdAt) {
        this.book = book;
        this.status = status;
        this.createdAt = createdAt;
    }

    public Book getBook() {
        return book;
    }

    public ReadingStatus getStatus() {
        return status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
