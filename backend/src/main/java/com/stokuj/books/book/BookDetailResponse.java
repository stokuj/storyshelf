package com.stokuj.books.book;

import com.stokuj.books.shelf.UserBookResponse;
import com.stokuj.books.book.ChapterResponse;
import com.stokuj.books.book.CharacterRelationResponse;
import com.stokuj.books.book.CharacterResponse;
import com.stokuj.books.review.ReviewResponse;

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
