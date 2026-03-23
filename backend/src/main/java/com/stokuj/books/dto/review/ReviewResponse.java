package com.stokuj.books.dto.review;

import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ReviewResponse {

    private Long id;
    private String username;
    private int rating;
    private String content;
    private Instant createdAt;
    private String bookTitle;
    private Long bookId;
}
