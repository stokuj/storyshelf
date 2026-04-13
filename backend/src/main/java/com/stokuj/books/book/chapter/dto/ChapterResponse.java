package com.stokuj.books.book.chapter.dto;

public record ChapterResponse(
        Long id,
        Long bookId,
        int chapterNumber,
        String title,
        boolean analysisCompleted,
        int charCount,
        int charCountClean,
        int wordCount,
        int tokenCount
) {}
