package com.stokuj.books.controller.api.admin;

import com.stokuj.books.dto.request.BookPatchRequest;
import com.stokuj.books.dto.request.BookRequest;
import com.stokuj.books.model.entity.Book;
import com.stokuj.books.service.BookChapterService;
import com.stokuj.books.service.BookService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin/books")
public class AdminBookApiController {

    private final BookService bookService;
    private final BookChapterService bookChapterService;

    public AdminBookApiController(BookService bookService, BookChapterService bookChapterService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
    }

    @PostMapping
    public Book create(@Valid @RequestBody BookRequest request) {
        return bookService.create(request);
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
}
