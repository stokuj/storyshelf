package com.stokuj.books.controller.api.admin;

import com.stokuj.books.domain.entity.Series;
import com.stokuj.books.dto.series.SeriesResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.SeriesRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin/series")
@Tag(name = "Series", description = "Admin endpoints for Series management")
public class AdminSeriesController {

    private final SeriesRepository seriesRepository;

    public AdminSeriesController(SeriesRepository seriesRepository) {
        this.seriesRepository = seriesRepository;
    }

    private SeriesResponse toDto(Series series) {
        return new SeriesResponse(series.getId(), series.getName(), series.getDescription(), null, series.getStatus());
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Create a new series")
    public ResponseEntity<SeriesResponse> create(@RequestBody Series series) {
        return ResponseEntity.status(201).body(toDto(seriesRepository.save(series)));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Update an existing series")
    public ResponseEntity<SeriesResponse> update(@PathVariable Long id, @RequestBody Series request) {
        Series existing = seriesRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Series not found"));
        existing.setName(request.getName());
        existing.setDescription(request.getDescription());
        existing.setStatus(request.getStatus());
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
