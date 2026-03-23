package com.stokuj.books.controller.api;

import com.stokuj.books.dto.chapter.ChapterResponse;
import com.stokuj.books.domain.entity.Chapter;
import com.stokuj.books.service.BookChapterService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/books/{bookId}/chapters")
public class ChapterController {

    private final BookChapterService bookChapterService;

    public ChapterController(BookChapterService bookChapterService) {
        this.bookChapterService = bookChapterService;
    }

    @GetMapping
    public ResponseEntity<List<ChapterResponse>> getChapters(@PathVariable Long bookId) {
        return ResponseEntity.ok(bookChapterService.getChapters(bookId));
    }

}