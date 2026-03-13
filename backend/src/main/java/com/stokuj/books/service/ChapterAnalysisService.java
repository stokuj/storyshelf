package com.stokuj.books.service;

import com.stokuj.books.client.StoryweaveClient;
import com.stokuj.books.dto.storyweave.AnalyseStats;
import com.stokuj.books.model.BookChapter;
import com.stokuj.books.repository.BookChapterRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
public class ChapterAnalysisService {

    private final BookChapterRepository chapterRepository;
    private final StoryweaveClient storyweaveClient;

    public ChapterAnalysisService(BookChapterRepository chapterRepository,
                                  StoryweaveClient storyweaveClient) {
        this.chapterRepository = chapterRepository;
        this.storyweaveClient = storyweaveClient;
    }

    @Async
    @Transactional
    public void analyseAsync(Long chapterId) {
        BookChapter chapter = chapterRepository.findById(chapterId).orElse(null);
        if (chapter == null) return;

        try {
            AnalyseStats stats = storyweaveClient.analyse(chapter.getContent());
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
}
