package com.stokuj.books.controller.fastapi;

import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.service.ChapterAnalysisService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/fastAPI")
public class FastApiController {

    private final BookChapterRepository chapterRepository;
    private final ChapterAnalysisService chapterAnalysisService;

    public FastApiController(BookChapterRepository chapterRepository,
                             ChapterAnalysisService chapterAnalysisService) {
        this.chapterRepository = chapterRepository;
        this.chapterAnalysisService = chapterAnalysisService;
    }

    @PostMapping("/chapters/{chapterId}/analyse")
    public ResponseEntity<Map<String, Object>> analyseChapter(@PathVariable Long chapterId) {
        if (!chapterRepository.existsById(chapterId)) {
            return ResponseEntity.notFound().build();
        }

        chapterAnalysisService.analyseAsync(chapterId);
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "analysis_started", true
        ));
    }

    @PostMapping("/chapters/{chapterId}/ner")
    public ResponseEntity<Map<String, Object>> nerChapter(@PathVariable Long chapterId) {
        if (!chapterRepository.existsById(chapterId)) {
            return ResponseEntity.notFound().build();
        }

        chapterAnalysisService.nerAsync(chapterId);
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "ner_started", true
        ));
    }
}
