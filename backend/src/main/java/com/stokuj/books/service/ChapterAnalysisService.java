package com.stokuj.books.service;

import com.stokuj.books.client.FastApiClient;
import com.stokuj.books.dto.fastapi.AnalyseStats;
import com.stokuj.books.dto.fastapi.NerTaskStatusResponse;
import com.stokuj.books.model.entity.BookChapter;
import com.stokuj.books.repository.BookChapterRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
public class ChapterAnalysisService {

    private static final int NER_MAX_ATTEMPTS = 30;
    private static final long NER_POLL_INTERVAL_MS = 30_000;

    private final BookChapterRepository chapterRepository;
    private final FastApiClient fastApiClient;

    public ChapterAnalysisService(BookChapterRepository chapterRepository,
                                  FastApiClient fastApiClient) {
        this.chapterRepository = chapterRepository;
        this.fastApiClient = fastApiClient;
    }

    @Async
    @Transactional
    public void analyseAsync(Long chapterId) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) return;

        try {
            AnalyseStats stats = fastApiClient.analyse(chapter.getContent());
            chapter.setCharCount(stats.charCount());
            chapter.setCharCountClean(stats.charCountClean());
            chapter.setWordCount(stats.wordCount());
            chapter.setTokenCount(stats.tokenCount());
            chapter.setAnalysisCompleted(true);
            chapterRepository.save(chapter);
        } catch (Exception e) {
            log.warn("Async analyse failed for chapter {}: {}", chapterId, e.getMessage());
        }
    }
    @Async
    @Transactional
    public void nerAsync(Long chapterId) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) return;

        String taskId;
        try {
            taskId = fastApiClient.startNer(chapter.getContent());
            log.info("NER task started for chapter {}: taskId={}", chapterId, taskId);
        } catch (Exception e) {
            log.warn("NER start failed for chapter {}: {}", chapterId, e.getMessage());
            return;
        }

        for (int attempt = 0; attempt < NER_MAX_ATTEMPTS; attempt++) {
            try {
                Thread.sleep(NER_POLL_INTERVAL_MS);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }

            try {
                NerTaskStatusResponse status = fastApiClient.pollNer(taskId);

                if ("FAILURE".equals(status.state())) {
                    log.warn("NER task failed for chapter {}: {}", chapterId, status.error());
                    return;
                }

                if (status.ready() && status.result() != null) {
                    chapter.setNerResult(status.result());
                    chapterRepository.save(chapter);
                    log.info("NER saved for chapter {}", chapterId);
                    return;
                }
            } catch (Exception e) {
                log.warn("NER poll error for chapter {}, attempt {}: {}", chapterId, attempt, e.getMessage());
            }
        }

        log.warn("NER timed out for chapter {} after {} attempts", chapterId, NER_MAX_ATTEMPTS);
    }
}
