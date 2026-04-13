package com.stokuj.books.series.dto;

import com.stokuj.books.series.SeriesStatus;

public record SeriesResponse(
        Long id,
        String name,
        String description,
        String coverUrl,
        SeriesStatus status
) {}
