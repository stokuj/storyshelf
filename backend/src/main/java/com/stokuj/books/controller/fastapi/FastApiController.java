package com.stokuj.books.controller.fastapi;

import com.stokuj.books.model.entity.Book;
import com.stokuj.books.model.entity.BookChapter;
import com.stokuj.books.model.fastapi.FindPairsResult;
import com.stokuj.books.repository.BookChapterRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.service.ChapterAnalysisService;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestBody;
import com.stokuj.books.dto.fastapi.AnalyseResponse;
import com.stokuj.books.model.fastapi.NerResult;
import com.stokuj.books.service.ChapterEventProducer;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/fastAPI")
public class FastApiController {

    private final BookChapterRepository chapterRepository;
    private final BookRepository bookRepository;
    private final ChapterAnalysisService chapterAnalysisService;
    private final ChapterEventProducer chapterEventProducer;

    public FastApiController(BookChapterRepository chapterRepository,
                             BookRepository bookRepository,
                             ChapterAnalysisService chapterAnalysisService,
                             ChapterEventProducer chapterEventProducer) {
        this.chapterRepository = chapterRepository;
        this.bookRepository = bookRepository;
        this.chapterAnalysisService = chapterAnalysisService;
        this.chapterEventProducer = chapterEventProducer;
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

    @PatchMapping("/chapters/{chapterId}/ner-result")
    @Transactional
    public ResponseEntity<Void> updateNerResult(@PathVariable Long chapterId,
                                                @RequestBody NerResult result) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) {
            return ResponseEntity.notFound().build();
        }

        chapter.setNerResult(result);
        chapterRepository.save(chapter);

        Book book = bookRepository.findByIdForUpdate(chapter.getBook().getId()).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }
        Map<String, Integer> current = book.getCharacters() != null ? book.getCharacters() : new HashMap<>();
        if (result.getCharacters() != null) {
            result.getCharacters().forEach((name, count) -> current.merge(name, count, Integer::sum));
        }
        book.setCharacters(current);
        book.setNerCompletedCount(book.getNerCompletedCount() + 1);
        bookRepository.save(book);

        boolean readyForFindPairs = book.getNerCompletedCount() >= book.getChaptersCount();
        if (!readyForFindPairs && chapter.getChapterNumber() == 1) {
            readyForFindPairs = true;
        }

        if (readyForFindPairs && book.getFindPairsResult() == null && current != null && !current.isEmpty()) {
            List<BookChapter> chapters = chapterRepository.findAllByBookIdOrderByChapterNumber(book.getId());
            String fullContent = chapters.stream()
                    .map(BookChapter::getContent)
                    .collect(Collectors.joining("\n\n"));
            chapterEventProducer.sendBookForFindPairs(book.getId(), fullContent, current);
        }

        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/find-pairs-result")
    public ResponseEntity<Void> updateBookFindPairsResult(@PathVariable Long bookId,
                                                          @RequestBody FindPairsResult result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        book.setFindPairsResult(result);
        bookRepository.save(book);

        if (result.getPairs() != null && !result.getPairs().isEmpty()) {
            chapterEventProducer.sendBookForRelations(bookId, result.getPairs());
        }

        return ResponseEntity.ok().build();
    }

    @PatchMapping("/books/{bookId}/relations-result")
    public ResponseEntity<Void> updateBookRelationsResult(@PathVariable Long bookId,
                                                          @RequestBody Map<String, Object> result) {
        Book book = bookRepository.findById(bookId).orElse(null);
        if (book == null) {
            return ResponseEntity.notFound().build();
        }

        book.setRelationsResult(result);
        bookRepository.save(book);

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
    public ResponseEntity<Void> findPairs(@PathVariable Long chapterId) {
        if (!chapterRepository.existsById(chapterId)) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.status(410).build();
    }
}
