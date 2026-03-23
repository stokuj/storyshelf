package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.Series;
import com.stokuj.books.dto.series.SeriesResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.SeriesRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.List;

@RestController
@RequestMapping("/api/series")
@Tag(name = "Series", description = "Operations related to book series")
public class SeriesController {

    private final SeriesRepository seriesRepository;

    public SeriesController(SeriesRepository seriesRepository) {
        this.seriesRepository = seriesRepository;
    }

    private SeriesResponse toDto(Series series) {
        return new SeriesResponse(series.getId(), series.getName(), series.getDescription(), null, series.getStatus());
    }

    @Operation(summary = "Get all series", description = "Retrieves a list of all book series.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved series list")
    @GetMapping
    public ResponseEntity<List<SeriesResponse>> getAll() {
        return ResponseEntity.ok(seriesRepository.findAll().stream().map(this::toDto).toList());
    }

    @Operation(summary = "Get series by ID", description = "Retrieves details of a specific book series by its ID.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved the series")
    @ApiResponse(responseCode = "404", description = "Series not found")
    @GetMapping("/{id}")
    public ResponseEntity<SeriesResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(
                toDto(seriesRepository.findById(id)
                        .orElseThrow(() -> new ResourceNotFoundException("Series not found")))
        );
    }

}