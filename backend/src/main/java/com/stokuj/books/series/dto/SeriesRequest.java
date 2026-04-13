package com.stokuj.books.series.dto;

import com.stokuj.books.series.SeriesStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SeriesRequest(
        @NotBlank(message = "Series name is required")
        @Size(max = 255, message = "Name cannot exceed 255 characters")
        String name,

        String description,

        @NotNull(message = "Status is required")
        SeriesStatus status
) {}
