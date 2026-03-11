package com.stokuj.books.controller;

import com.stokuj.books.dto.BookPatchRequest;
import com.stokuj.books.dto.BookRequest;
import com.stokuj.books.model.Book;
import com.stokuj.books.service.BookService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books")
public class BookController {

    private final BookService bookService;

    public BookController(BookService bookService) {
        this.bookService = bookService;
    }

    
    @GetMapping
    public List<Book> getAll() {
        return bookService.getAll();
    }

    @PostMapping
    public Book create(@Valid @RequestBody BookRequest request) {
        return bookService.create(request);
    }

    @GetMapping("/{id}")
    public Book getById(@PathVariable Long id) {
        return bookService.getById(id);
    }

    @PutMapping("/{id}")
    public Book update(@PathVariable Long id, @Valid @RequestBody BookRequest request) {
        return bookService.update(id, request);
    }

    @PatchMapping("/{id}")
    public Book patch(@PathVariable Long id, @Valid @RequestBody BookPatchRequest request) {
        return bookService.patch(id, request);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        bookService.delete(id);
    }
}
