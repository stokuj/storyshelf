package com.stokuj.books.dto.series;

import com.stokuj.books.domain.enums.SeriesStatus;

public record SeriesResponse(
        Long id,
        String name,
        String description,
        String coverUrl,
        SeriesStatus status
) {}