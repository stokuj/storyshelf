package com.stokuj.books.analysis;

import com.stokuj.books.book.Book;
import com.stokuj.books.book.Chapter;
import com.stokuj.books.analysis.AnalyseResponse;
import com.stokuj.books.analysis.BookFindPairsResult;
import com.stokuj.books.book.BookChapterRepository;
import com.stokuj.books.book.BookRepository;
import com.stokuj.books.analysis.ChapterEventProducer;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import com.stokuj.books.analysis.NerResult;
import com.stokuj.books.analysis.NerResultProcessor;
import com.stokuj.books.analysis.RelationsResultProcessor;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.Map;

@RestController
@RequestMapping("/api/fastapi")
@Tag(name = "Integration (FastAPI)", description = "Webhooks and triggers for asynchronous NLP analysis (Named Entity Recognition, statistics, relations) handled by an external FastAPI worker.")
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

    @Operation(summary = "Receive chapter statistics results", description = "Webhook used by FastAPI to save text analysis results (e.g. word count, characters, tokens).")
    @ApiResponse(responseCode = "200", description = "Statistics updated successfully")
    @ApiResponse(responseCode = "404", description = "Chapter not found")
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

    @Operation(summary = "Receive NER (Named Entity Recognition) results", description = "Webhook used by FastAPI to process and save recognized entities (mainly characters) in a chapter.")
    @ApiResponse(responseCode = "200", description = "NER results processed and saved")
    @ApiResponse(responseCode = "404", description = "Chapter not found")
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

    @Operation(summary = "Receive character pairs for relation analysis", description = "Webhook used by FastAPI to receive initially identified character pairs in a book.")
    @ApiResponse(responseCode = "200", description = "Character pairs saved successfully")
    @ApiResponse(responseCode = "404", description = "Book not found")
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

    @Operation(summary = "Receive character relations results", description = "Webhook used by FastAPI to save sentiment/type of relations between characters.")
    @ApiResponse(responseCode = "200", description = "Character relations saved successfully")
    @ApiResponse(responseCode = "404", description = "Book not found")
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

    @Operation(summary = "Trigger basic text analysis", description = "Sends an event to a Kafka queue to asynchronously calculate chapter statistics (like word count).")
    @ApiResponse(responseCode = "202", description = "Analysis task accepted")
    @ApiResponse(responseCode = "404", description = "Chapter not found")
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

    @Operation(summary = "Trigger NER analysis", description = "Sends an event to a Kafka queue to asynchronously find and match characters in the chapter text.")
    @ApiResponse(responseCode = "202", description = "NER analysis task accepted")
    @ApiResponse(responseCode = "404", description = "Chapter not found")
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
