package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.Author;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.AuthorRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/authors")
public class AuthorController {

    private final AuthorRepository authorRepository;

    public AuthorController(AuthorRepository authorRepository) {
        this.authorRepository = authorRepository;
    }

    @GetMapping
    public ResponseEntity<List<Author>> getAll() {
        return ResponseEntity.ok(authorRepository.findAll());
    }

    @GetMapping("/{id}")
    public ResponseEntity<Author> getById(@PathVariable Long id) {
        return ResponseEntity.ok(
                authorRepository.findById(id)
                        .orElseThrow(() -> new ResourceNotFoundException("Author not found"))
        );
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Author> create(@RequestBody Author author) {
        return ResponseEntity.status(201).body(authorRepository.save(author));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Author> update(@PathVariable Long id, @RequestBody Author request) {
        Author existing = authorRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Author not found"));
        existing.setName(request.getName());
        existing.setBio(request.getBio());
        existing.setBirthDate(request.getBirthDate());
        return ResponseEntity.ok(authorRepository.save(existing));
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        authorRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}