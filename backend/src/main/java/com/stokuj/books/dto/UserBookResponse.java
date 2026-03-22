package com.stokuj.books.dto;

import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.enums.ReadingStatus;

import java.time.Instant;

public class UserBookResponse {

    private final Book book;
    private final ReadingStatus status;
    private final Instant createdAt;

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
