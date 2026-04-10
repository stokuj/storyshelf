package com.stokuj.books.series;

import com.stokuj.books.series.Series;
import com.stokuj.books.series.SeriesRequest;
import com.stokuj.books.series.SeriesResponse;
import com.stokuj.books.core.ResourceNotFoundException;
import com.stokuj.books.series.SeriesRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/moderator/series")
@Tag(name = "Moderator - Series", description = "Moderator endpoints for series management")
public class ModeratorSeriesController {

    private final SeriesRepository seriesRepository;

    public ModeratorSeriesController(SeriesRepository seriesRepository) {
        this.seriesRepository = seriesRepository;
    }

    private SeriesResponse toDto(Series series) {
        return new SeriesResponse(series.getId(), series.getName(), series.getDescription(), null, series.getStatus());
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Create a new series")
    public ResponseEntity<SeriesResponse> create(@Valid @RequestBody SeriesRequest request) {
        Series series = new Series();
        series.setName(request.name());
        series.setDescription(request.description());
        series.setStatus(request.status());
        return ResponseEntity.status(201).body(toDto(seriesRepository.save(series)));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Update an existing series")
    public ResponseEntity<SeriesResponse> update(@PathVariable Long id, @Valid @RequestBody SeriesRequest request) {
        Series existing = seriesRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Series not found"));
        existing.setName(request.name());
        existing.setDescription(request.description());
        existing.setStatus(request.status());
        return ResponseEntity.ok(toDto(seriesRepository.save(existing)));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Delete a series")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        seriesRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
