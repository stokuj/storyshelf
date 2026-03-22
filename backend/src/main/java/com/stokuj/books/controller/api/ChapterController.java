package com.stokuj.books.controller.api;

import com.stokuj.books.domain.entity.Chapter;
import com.stokuj.books.service.BookChapterService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/books/{bookId}/chapters")
public class ChapterController {

    private final BookChapterService bookChapterService;

    public ChapterController(BookChapterService bookChapterService) {
        this.bookChapterService = bookChapterService;
    }

    @GetMapping
    public ResponseEntity<List<Chapter>> getChapters(@PathVariable Long bookId) {
        return ResponseEntity.ok(bookChapterService.getChapters(bookId));
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Map<String, Object>> uploadContent(@PathVariable Long bookId,
                                                             @RequestParam("file") MultipartFile file) throws IOException {
        String content = new String(file.getBytes(), StandardCharsets.UTF_8).strip();
        int count = bookChapterService.loadContent(bookId, content);
        return ResponseEntity.status(201).body(Map.of(
                "bookId", bookId,
                "chaptersCreated", count
        ));
    }

    @DeleteMapping
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> clearContent(@PathVariable Long bookId) {
        bookChapterService.clearContent(bookId);
        return ResponseEntity.noContent().build();
    }
}