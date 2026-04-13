package com.stokuj.books.author;

import com.stokuj.books.author.Author;
import com.stokuj.books.author.dto.AuthorRequest;
import com.stokuj.books.author.dto.AuthorResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.author.AuthorRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/authors")
@Tag(name = "Authors", description = "Operations related to authors")
public class AuthorController {

    private final AuthorRepository authorRepository;

    public AuthorController(AuthorRepository authorRepository) {
        this.authorRepository = authorRepository;
    }

    private AuthorResponse toDto(Author author) {
        return new AuthorResponse(author.getId(), author.getName(), author.getBio(), null, author.getBirthDate());
    }

    @Operation(summary = "Get a list of all authors")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved list of authors")
    @GetMapping
    public ResponseEntity<List<AuthorResponse>> getAll() {
        return ResponseEntity.ok(authorRepository.findAll().stream().map(this::toDto).toList());
    }

    @Operation(summary = "Get an author by ID")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved the author")
    @ApiResponse(responseCode = "404", description = "Author not found")
    @GetMapping("/{id}")
    public ResponseEntity<AuthorResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(
                toDto(authorRepository.findById(id)
                        .orElseThrow(() -> new ResourceNotFoundException("Author not found")))
        );
    }

    @Operation(summary = "Create a new author")
    @ApiResponse(responseCode = "201", description = "Author created successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<AuthorResponse> create(@Valid @RequestBody AuthorRequest request) {
        Author author = new Author();
        author.setName(request.name());
        author.setBio(request.bio());
        author.setBirthDate(request.birthDate());
        return ResponseEntity.status(201).body(toDto(authorRepository.save(author)));
    }

    @Operation(summary = "Update an existing author")
    @ApiResponse(responseCode = "200", description = "Author updated successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @ApiResponse(responseCode = "404", description = "Author not found")
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<AuthorResponse> update(@PathVariable Long id, @Valid @RequestBody AuthorRequest request) {
        Author existing = authorRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Author not found"));
        existing.setName(request.name());
        existing.setBio(request.bio());
        existing.setBirthDate(request.birthDate());
        return ResponseEntity.ok(toDto(authorRepository.save(existing)));
    }

    @Operation(summary = "Delete an author by ID")
    @ApiResponse(responseCode = "204", description = "Author deleted successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        authorRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }
}
