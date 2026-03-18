package com.stokuj.books.controller.fastapi;

import com.stokuj.books.client.FastApiClient;
import com.stokuj.books.dto.fastapi.FindPairsRequest;
import com.stokuj.books.model.entity.BookChapter;
import com.stokuj.books.model.fastapi.FindPairsResult;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.service.ChapterAnalysisService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import com.stokuj.books.dto.fastapi.AnalyseResponse;

import java.util.Map;

@RestController
@RequestMapping("/api/fastAPI")
public class FastApiController {

    private final BookChapterRepository chapterRepository;
    private final ChapterAnalysisService chapterAnalysisService;
    private final FastApiClient fastApiClient;

    public FastApiController(BookChapterRepository chapterRepository,
                             ChapterAnalysisService chapterAnalysisService,
                             FastApiClient fastApiClient) {
        this.chapterRepository = chapterRepository;
        this.chapterAnalysisService = chapterAnalysisService;
        this.fastApiClient = fastApiClient;
    }

    @PatchMapping("/chapters/{chapterId}/analyse-result")
    public ResponseEntity<Void> updateAnalyseResult(@PathVariable Long chapterId,
                                                    @RequestBody AnalyseResponse result) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapter.setCharCount(result.analysis().charCount());
        chapter.setCharCountClean(result.analysis().charCountClean());
        chapter.setWordCount(result.analysis().wordCount());
        chapter.setTokenCount(result.analysis().tokenCount());
        chapter.setAnalysisCompleted(true);

        chapterRepository.save(chapter);

        return ResponseEntity.ok().build();
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

    @PostMapping("/chapters/{chapterId}/find-pairs")
    public ResponseEntity<FindPairsResult> findPairs(@PathVariable Long chapterId,
                                                     @Valid @RequestBody FindPairsRequest request) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        FindPairsResult result = fastApiClient.findPairs(chapter.getContent(), request.names());
        chapter.setFindPairsResult(result);
        chapterRepository.save(chapter);

        return ResponseEntity.ok(result);
    }
}
