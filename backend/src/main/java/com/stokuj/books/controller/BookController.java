package com.stokuj.books.controller;

import com.stokuj.books.dto.BookPatchRequest;
import com.stokuj.books.dto.BookRequest;
import com.stokuj.books.model.Book;
import com.stokuj.books.model.BookChapter;
import com.stokuj.books.service.BookChapterService;
import com.stokuj.books.service.BookService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;


@RestController
@RequestMapping("/api/books")
public class BookController {

    private final BookService bookService;

    private final BookChapterService bookChapterService;

    public BookController(BookService bookService, BookChapterService bookChapterService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
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


    @PostMapping(path = "/{id}/content", consumes = "text/plain")
    public ResponseEntity<Map<String, Object>> uploadContent(
            @PathVariable Long id,
            @NotBlank @RequestBody String content) {

        int chaptersCount = bookChapterService.loadContent(id, content);
        return ResponseEntity.ok(Map.of(
                "book_id", id,
                "chapters_loaded", chaptersCount
        ));
    }

    @GetMapping("/{id}/content")
    public ResponseEntity<List<BookChapter>> getContent(@PathVariable Long id) {
        return ResponseEntity.ok(bookChapterService.getChapters(id));
    }

    @DeleteMapping("/{id}/content")
    public ResponseEntity<Void> clearContent(@PathVariable Long id) {
        bookChapterService.clearContent(id);
        return ResponseEntity.noContent().build();
    }
}
