package com.stokuj.books.dto.response;

import java.time.Instant;

public record ReviewResponse(
        Long id,
        String username,
        int rating,
        String content,
        Instant createdAt,
        String bookTitle,
        Long bookId
) {
}
