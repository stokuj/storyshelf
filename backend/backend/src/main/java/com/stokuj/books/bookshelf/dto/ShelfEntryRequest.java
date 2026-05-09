package com.stokuj.books.bookshelf.dto;

import com.stokuj.books.bookshelf.ReadingStatus;
import jakarta.validation.constraints.NotNull;

public record ShelfEntryRequest(
        @NotNull(message = "Status is required")
        ReadingStatus status
) {}