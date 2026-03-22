package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.Series;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.SeriesRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/series")
public class SeriesController {

    private final SeriesRepository seriesRepository;

    public SeriesController(SeriesRepository seriesRepository) {
        this.seriesRepository = seriesRepository;
    }

    @GetMapping
    public ResponseEntity<List<Series>> getAll() {
        return ResponseEntity.ok(seriesRepository.findAll());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Series> getById(@PathVariable Long id) {
        return ResponseEntity.ok(
                seriesRepository.findById(id)
                        .orElseThrow(() -> new ResourceNotFoundException("Series not found"))
        );
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Series> create(@RequestBody Series series) {
        return ResponseEntity.status(201).body(seriesRepository.save(series));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Series> update(@PathVariable Long id, @RequestBody Series request) {
        Series existing = seriesRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Series not found"));
        existing.setName(request.getName());
        existing.setDescription(request.getDescription());
        existing.setStatus(request.getStatus());
        return ResponseEntity.ok(seriesRepository.save(existing));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        seriesRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}