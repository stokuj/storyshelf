package com.stokuj.books.controller.api.admin;

import com.stokuj.books.domain.entity.Author;
import com.stokuj.books.dto.author.AuthorRequest;
import com.stokuj.books.dto.author.AuthorResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.AuthorRepository;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin/authors")
@Tag(name = "Authors", description = "Administrative operations related to authors")
public class AdminAuthorController {

    private final AuthorRepository authorRepository;

    public AdminAuthorController(AuthorRepository authorRepository) {
        this.authorRepository = authorRepository;
    }

    private AuthorResponse toDto(Author author) {
        return new AuthorResponse(author.getId(), author.getName(), author.getBio(), null, author.getBirthDate());
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