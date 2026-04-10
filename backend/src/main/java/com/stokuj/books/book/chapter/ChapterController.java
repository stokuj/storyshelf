package com.stokuj.books.book.chapter;

import com.stokuj.books.book.chapter.ChapterResponse;
import com.stokuj.books.book.chapter.Chapter;
import com.stokuj.books.book.chapter.BookChapterService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/books/{bookId}/chapters")
@Tag(name = "Chapters", description = "Operations related to book chapters")
public class ChapterController {

    private final BookChapterService bookChapterService;

    public ChapterController(BookChapterService bookChapterService) {
        this.bookChapterService = bookChapterService;
    }

    @Operation(summary = "Get chapters for a book", description = "Retrieves a list of all chapters for a specific book.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved chapters")
    @GetMapping
    public ResponseEntity<List<ChapterResponse>> getChapters(@PathVariable Long bookId) {
        return ResponseEntity.ok(bookChapterService.getChapters(bookId));
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
