package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.Series;
import com.stokuj.books.dto.series.SeriesResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.SeriesRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/series")
public class SeriesController {

    private final SeriesRepository seriesRepository;

    public SeriesController(SeriesRepository seriesRepository) {
        this.seriesRepository = seriesRepository;
    }

    private SeriesResponse toDto(Series series) {
        return new SeriesResponse(series.getId(), series.getName(), series.getDescription(), null, series.getStatus());
    }

    @GetMapping
    public ResponseEntity<List<SeriesResponse>> getAll() {
        return ResponseEntity.ok(seriesRepository.findAll().stream().map(this::toDto).toList());
    }

    @GetMapping("/{id}")
    public ResponseEntity<SeriesResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(
                toDto(seriesRepository.findById(id)
                        .orElseThrow(() -> new ResourceNotFoundException("Series not found")))
        );
    }

}