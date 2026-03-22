package com.stokuj.books.dto.bookshelf;

import com.stokuj.books.domain.enums.ReadingStatus;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UserBookRequest {

    private ReadingStatus status;
}
