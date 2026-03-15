package com.stokuj.books.controller;

import com.stokuj.books.dto.request.UserBookRequest;
import com.stokuj.books.dto.response.UserBookResponse;
import com.stokuj.books.service.UserBookService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/me/books")
public class UserBookController {

    private final UserBookService userBookService;

    public UserBookController(UserBookService userBookService) {
        this.userBookService = userBookService;
    }

    @GetMapping
    public List<UserBookResponse> getMyBooks(Authentication authentication) {
        return userBookService.getMyBooks(authentication.getName());
    }

    @PostMapping("/{bookId}")
    public UserBookResponse addToShelf(
            @PathVariable Long bookId,
            @RequestBody(required = false) UserBookRequest request,
            Authentication authentication) {
        return userBookService.addToShelf(authentication.getName(), bookId, request);
    }

    @PutMapping("/{bookId}")
    public UserBookResponse updateStatus(
            @PathVariable Long bookId,
            @RequestBody UserBookRequest request,
            Authentication authentication) {
        return userBookService.updateStatus(authentication.getName(), bookId, request);
    }

    @DeleteMapping("/{bookId}")
    public void removeFromShelf(@PathVariable Long bookId, Authentication authentication) {
        userBookService.removeFromShelf(authentication.getName(), bookId);
    }
}
