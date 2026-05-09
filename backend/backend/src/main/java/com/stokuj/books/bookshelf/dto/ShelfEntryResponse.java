package com.stokuj.books.bookshelf.dto;

import com.stokuj.books.bookshelf.ReadingStatus;
import java.time.Instant;

public record ShelfEntryResponse(
    BookSummary book,
    ReadingStatus status,
    Instant createdAt
) {

    public record BookSummary(Long id, String title, String author) {}
}
