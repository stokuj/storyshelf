package com.stokuj.books.controller;

import com.stokuj.books.model.Book;
import com.stokuj.books.service.UserBookService;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
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
    public List<Book> getMyReadBooks(Authentication authentication) {
        return userBookService.getMyReadBooks(authentication.getName());
    }

    @PostMapping("/{bookId}")
    public Book markAsRead(@PathVariable Long bookId, Authentication authentication) {
        return userBookService.markAsRead(authentication.getName(), bookId);
    }

    @DeleteMapping("/{bookId}")
    public void unmarkAsRead(@PathVariable Long bookId, Authentication authentication) {
        userBookService.unmarkAsRead(authentication.getName(), bookId);
    }
}
