package com.stokuj.books.series.dto;

import com.stokuj.books.series.SeriesStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SeriesRequest(
        @NotBlank(message = "Series name is required")
        @Size(min = 10, max = 255, message = "Name must be between 10 and 255 characters long")
        String name,

        String description,

        @NotNull(message = "Status is required")
        SeriesStatus status
) {}
