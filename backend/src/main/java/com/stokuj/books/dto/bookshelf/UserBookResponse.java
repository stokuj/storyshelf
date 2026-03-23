package com.stokuj.books.dto.bookshelf;

import com.stokuj.books.domain.enums.ReadingStatus;
import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class UserBookResponse {

    public record BookSummary(Long id, String title, String author) {}

    private BookSummary book;
    private ReadingStatus status;
    private Instant createdAt;
}
