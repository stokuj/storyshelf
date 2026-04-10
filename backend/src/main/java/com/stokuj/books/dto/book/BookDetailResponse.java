package com.stokuj.books.dto.book;

import com.stokuj.books.dto.bookshelf.UserBookResponse;
import com.stokuj.books.dto.chapter.ChapterResponse;
import com.stokuj.books.dto.character.CharacterRelationResponse;
import com.stokuj.books.dto.character.CharacterResponse;
import com.stokuj.books.dto.review.ReviewResponse;

import java.util.List;

public record BookDetailResponse(
        BookResponse book,
        AnalysisStatusResponse analysisStatus,
        UserBookResponse shelfEntry,
        List<ChapterResponse> chapters,
        List<CharacterResponse> characters,
        List<CharacterRelationResponse> relations,
        List<ReviewResponse> reviews
) {
    public record AnalysisStatusResponse(
            int chaptersCount,
            int nerCompletedCount,
            boolean analysisFinished
    ) {
    }
}
