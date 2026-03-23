package com.stokuj.books.controller.api.admin;

import com.stokuj.books.service.BookChapterService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;

@RestController
@RequestMapping("/api/admin/books/{bookId}/chapters")
@Tag(name = "Chapters", description = "Admin endpoints for Chapter management")
public class AdminChapterController {

    private final BookChapterService bookChapterService;

    public AdminChapterController(BookChapterService bookChapterService) {
        this.bookChapterService = bookChapterService;
    }

    @PostMapping
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Upload chapter content")
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
    @Operation(summary = "Clear chapter content")
    public ResponseEntity<Void> clearContent(@PathVariable Long bookId) {
        bookChapterService.clearContent(bookId);
        return ResponseEntity.noContent().build();
    }
}
