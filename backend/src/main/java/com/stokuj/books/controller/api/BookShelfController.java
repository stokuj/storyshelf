package com.stokuj.books.controller.api;

import com.stokuj.books.dto.bookshelf.UserBookRequest;
import com.stokuj.books.dto.bookshelf.UserBookResponse;
import com.stokuj.books.service.UserBookService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/shelf")
@PreAuthorize("hasRole('USER')")
public class BookShelfController {

    private final UserBookService userBookService;

    public BookShelfController(UserBookService userBookService) {
        this.userBookService = userBookService;
    }

    @GetMapping
    public ResponseEntity<List<UserBookResponse>> getMyBooks(Authentication authentication) {
        return ResponseEntity.ok(userBookService.getMyBooks(authentication.getName()));
    }

    @PostMapping("/{bookId}")
    public ResponseEntity<UserBookResponse> addToShelf(@PathVariable Long bookId,
                                                       @RequestBody(required = false) UserBookRequest request,
                                                       Authentication authentication) {
        return ResponseEntity.status(201)
                .body(userBookService.addToShelf(authentication.getName(), bookId, request));
    }

    @PatchMapping("/{bookId}")
    public ResponseEntity<UserBookResponse> updateStatus(@PathVariable Long bookId,
                                                         @RequestBody UserBookRequest request,
                                                         Authentication authentication) {
        return ResponseEntity.ok(userBookService.updateStatus(authentication.getName(), bookId, request));
    }

    @DeleteMapping("/{bookId}")
    public ResponseEntity<Void> removeFromShelf(@PathVariable Long bookId,
                                                Authentication authentication) {
        userBookService.removeFromShelf(authentication.getName(), bookId);
        return ResponseEntity.noContent().build();
    }
}