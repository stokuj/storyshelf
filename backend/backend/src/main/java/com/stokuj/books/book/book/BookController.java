package com.stokuj.books.book.book;

import com.stokuj.books.book.book.dto.BookDetailResponse;
import com.stokuj.books.book.book.dto.BookPatchRequest;
import com.stokuj.books.book.book.dto.BookRequest;
import com.stokuj.books.book.book.dto.BookResponse;
import com.stokuj.books.book.book.BookDetailService;
import com.stokuj.books.book.book.BookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books")
@Tag(name = "Books", description = "Operations related to books management")
public class BookController {

    private final BookService bookService;
    private final BookDetailService bookDetailService;

    public BookController(BookService bookService, BookDetailService bookDetailService) {
        this.bookService = bookService;
        this.bookDetailService = bookDetailService;
    }

    @Operation(summary = "Search books by title, author, or genre")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved list of books")
    @GetMapping
    public ResponseEntity<List<BookResponse>> search(@RequestParam(required = false) String q) {
        return ResponseEntity.ok(bookService.search(q));
    }

    @Operation(summary = "Get a book by its ID")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved the book")
    @ApiResponse(responseCode = "404", description = "Book not found")
    @GetMapping("/{id}")
    public ResponseEntity<BookResponse> getById(@PathVariable Long id) {
        return ResponseEntity.ok(bookService.getById(id));
    }

    @Operation(summary = "Get complete book details for the frontend")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved aggregated book details")
    @ApiResponse(responseCode = "404", description = "Book not found")
    @GetMapping("/{id}/details")
    public ResponseEntity<BookDetailResponse> getDetails(@PathVariable Long id, Authentication authentication) {
        String email = authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken)
                ? authentication.getName()
                : null;
        return ResponseEntity.ok(bookDetailService.getById(id, email));
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
