package com.stokuj.books.book;

import com.stokuj.books.book.BookDetailResponse;
import com.stokuj.books.book.BookResponse;
import com.stokuj.books.book.BookDetailService;
import com.stokuj.books.book.BookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
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

}
