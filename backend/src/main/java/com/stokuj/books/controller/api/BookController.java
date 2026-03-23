package com.stokuj.books.controller.api;

import com.stokuj.books.dto.book.BookResponse;
import com.stokuj.books.service.BookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books")
@Tag(name = "Books", description = "Operations related to books management")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
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

}