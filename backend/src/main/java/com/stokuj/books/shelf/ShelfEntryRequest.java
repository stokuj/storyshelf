package com.stokuj.books.shelf;

import com.stokuj.books.shelf.ReadingStatus;
import lombok.Getter;
import lombok.Setter;
import jakarta.validation.constraints.NotNull;

@Getter
@Setter
public class ShelfEntryRequest {

    @NotNull(message = "Status is required")
    private ReadingStatus status;
}
