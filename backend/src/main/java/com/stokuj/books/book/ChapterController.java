package com.stokuj.books.book;

import com.stokuj.books.book.ChapterResponse;
import com.stokuj.books.book.Chapter;
import com.stokuj.books.book.BookChapterService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.List;

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

}
