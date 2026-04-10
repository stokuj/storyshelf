package com.stokuj.books.book;

import com.stokuj.books.book.BookPatchRequest;
import com.stokuj.books.book.BookRequest;
import com.stokuj.books.book.BookResponse;
import com.stokuj.books.book.BookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/moderator/books")
@Tag(name = "Moderator - Books", description = "Moderator endpoints for books management")
public class ModeratorBookController {

    private final BookService bookService;

    public ModeratorBookController(BookService bookService) {
        this.bookService = bookService;
    }

    @Operation(summary = "Create a new book")
    @ApiResponse(responseCode = "201", description = "Book created successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<BookResponse> create(@Valid @RequestBody BookRequest request) {
        return ResponseEntity.status(201).body(bookService.create(request));
    }

    @Operation(summary = "Update an existing book completely")
    @ApiResponse(responseCode = "200", description = "Book updated successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @ApiResponse(responseCode = "404", description = "Book not found")
    @PutMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<BookResponse> update(@PathVariable Long id, @Valid @RequestBody BookRequest request) {
        return ResponseEntity.ok(bookService.update(id, request));
    }

    @Operation(summary = "Update specific fields of an existing book")
    @ApiResponse(responseCode = "200", description = "Book patched successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @ApiResponse(responseCode = "404", description = "Book not found")
    @PatchMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<BookResponse> patch(@PathVariable Long id, @Valid @RequestBody BookPatchRequest request) {
        return ResponseEntity.ok(bookService.patch(id, request));
    }

    @Operation(summary = "Delete a book by its ID")
    @ApiResponse(responseCode = "204", description = "Book deleted successfully (No content)")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @ApiResponse(responseCode = "403", description = "Forbidden - requires MODERATOR role")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        bookService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
