package com.stokuj.books.dto.bookshelf;

import com.stokuj.books.domain.enums.ReadingStatus;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.NotNull;

@Getter
@Setter
public class UserBookRequest {

    @NotNull(message = "Status is required")
    private ReadingStatus status;
}
