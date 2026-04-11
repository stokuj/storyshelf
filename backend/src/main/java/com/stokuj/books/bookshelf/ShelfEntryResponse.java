package com.stokuj.books.bookshelf;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ShelfEntryResponse {

    public record BookSummary(Long id, String title, String author) {}

    private BookSummary book;
    private ReadingStatus status;
    private Instant createdAt;
}
