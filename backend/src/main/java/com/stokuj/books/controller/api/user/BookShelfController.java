package com.stokuj.books.controller.api.user;

import com.stokuj.books.dto.bookshelf.UserBookRequest;
import com.stokuj.books.dto.bookshelf.UserBookResponse;
import com.stokuj.books.service.UserBookService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/shelf")
@PreAuthorize("hasRole('USER')")
@Tag(name = "Bookshelf", description = "Operations for users to manage their personal book collections")
public class BookShelfController {

    private final UserBookService userBookService;

    public BookShelfController(UserBookService userBookService) {
        this.userBookService = userBookService;
    }

    @Operation(summary = "Get user's bookshelf", description = "Retrieves a list of all books added to the authenticated user's shelf.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved bookshelf")
    @GetMapping
    public ResponseEntity<List<UserBookResponse>> getMyBooks(Authentication authentication) {
        return ResponseEntity.ok(userBookService.getMyBooks(authentication.getName()));
    }

    @Operation(summary = "Add book to shelf", description = "Adds a specific book to the authenticated user's shelf.")
    @ApiResponse(responseCode = "201", description = "Book added to shelf successfully")
    @PostMapping("/{bookId}")
    public ResponseEntity<UserBookResponse> addToShelf(@PathVariable Long bookId,
                                                       @Valid @RequestBody(required = false) UserBookRequest request,
                                                       Authentication authentication) {
        return ResponseEntity.status(201)
                .body(userBookService.addToShelf(authentication.getName(), bookId, request));
    }

    @Operation(summary = "Get bookshelf entry for a book", description = "Retrieves the authenticated user's shelf entry for a specific book.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved bookshelf entry")
    @ApiResponse(responseCode = "404", description = "Book is not on the user's shelf")
    @GetMapping("/{bookId}")
    public ResponseEntity<UserBookResponse> getShelfEntry(@PathVariable Long bookId,
                                                          Authentication authentication) {
        return userBookService.findByUserAndBook(authentication.getName(), bookId)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.status(HttpStatus.NOT_FOUND).build());
    }

    @Operation(summary = "Update book status on shelf", description = "Updates the reading status or progress of a book on the user's shelf.")
    @ApiResponse(responseCode = "200", description = "Status updated successfully")
    @PatchMapping("/{bookId}")
    public ResponseEntity<UserBookResponse> updateStatus(@PathVariable Long bookId,
                                                         @Valid @RequestBody UserBookRequest request,
                                                         Authentication authentication) {
        return ResponseEntity.ok(userBookService.updateStatus(authentication.getName(), bookId, request));
    }

    @Operation(summary = "Remove book from shelf", description = "Removes a specific book from the authenticated user's shelf.")
    @ApiResponse(responseCode = "204", description = "Book removed successfully")
    @DeleteMapping("/{bookId}")
    public ResponseEntity<Void> removeFromShelf(@PathVariable Long bookId,
                                                Authentication authentication) {
        userBookService.removeFromShelf(authentication.getName(), bookId);
        return ResponseEntity.noContent().build();
    }
}
