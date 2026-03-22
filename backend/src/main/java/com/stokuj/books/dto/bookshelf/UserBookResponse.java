package com.stokuj.books.dto.bookshelf;

import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.enums.ReadingStatus;
import java.time.Instant;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class UserBookResponse {

    private Book book;
    private ReadingStatus status;
    private Instant createdAt;
}
