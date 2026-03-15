package com.stokuj.books.dto.fastapi;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;

import java.util.List;

public record FindPairsRequest(
        @NotEmpty
        @Size(min = 2)
        List<String> names
) {
}
