package com.stokuj.books.controller.integration;

import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.entity.Chapter;
import com.stokuj.books.dto.integration.AnalyseResponse;
import com.stokuj.books.dto.integration.BookFindPairsResult;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.integration.kafka.ChapterEventProducer;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import com.stokuj.books.dto.integration.NerResult;
import com.stokuj.books.integration.processor.NerResultProcessor;
import com.stokuj.books.integration.processor.RelationsResultProcessor;

import java.util.Map;

@RestController
@RequestMapping("/api/fastapi")
public class FastApiCallbackController {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final ChapterEventProducer chapterEventProducer;
    private final NerResultProcessor nerResultProcessor;
    private final RelationsResultProcessor relationsResultProcessor;

    public FastApiCallbackController(BookChapterRepository chapterRepository,
                                     BookRepository bookRepository,
                                     ChapterEventProducer chapterEventProducer,
                                     NerResultProcessor nerResultProcessor,
                                     RelationsResultProcessor relationsResultProcessor) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.chapterEventProducer = chapterEventProducer;
        this.nerResultProcessor = nerResultProcessor;
        this.relationsResultProcessor = relationsResultProcessor;
    }

    @PatchMapping("/chapters/{chapterId}/analyse-result")
    public ResponseEntity<Void> updateAnalyseResult(@PathVariable Long chapterId,
                                                    @RequestBody AnalyseResponse result) {
        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
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

    @PatchMapping("/chapters/{chapterId}/ner-result")
    @Transactional
    public ResponseEntity<Void> updateNerResult(@PathVariable Long chapterId,
                                                @RequestBody NerResult result) {
        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        nerResultProcessor.process(chapter, result);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/find-pairs-result")
    public ResponseEntity<Void> updateBookFindPairsResult(@PathVariable Long bookId,
                                                          @RequestBody BookFindPairsResult result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        relationsResultProcessor.processFindPairsResult(book, result);
        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/relations-result")
    public ResponseEntity<Void> updateBookRelationsResult(@PathVariable Long bookId,
                                                          @RequestBody Map<String, Object> result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        relationsResultProcessor.processRelationsResult(book, result);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/chapters/{chapterId}/analyse")
    public ResponseEntity<Map<String, Object>> analyseChapter(@PathVariable Long chapterId) {
        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapterEventProducer.sendChapterForAnalysis(chapter.getId(), chapter.getContent());
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "analysis_started", true
        ));
    }

    @PostMapping("/chapters/{chapterId}/ner")
    public ResponseEntity<Map<String, Object>> nerChapter(@PathVariable Long chapterId) {
        Chapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapterEventProducer.sendChapterForNer(chapter.getId(), chapter.getContent());
        return ResponseEntity.accepted().body(Map.of(
                "chapter_id", chapterId,
                "ner_started", true
        ));
    }



}
