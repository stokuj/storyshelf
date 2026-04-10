package com.stokuj.books.book.book;

import com.stokuj.books.shelf.ShelfEntryResponse;
import com.stokuj.books.book.chapter.ChapterResponse;
import com.stokuj.books.book.character.CharacterRelationResponse;
import com.stokuj.books.book.character.CharacterResponse;
import com.stokuj.books.review.ReviewResponse;

import java.util.List;

public record BookDetailResponse(
        BookResponse book,
        AnalysisStatusResponse analysisStatus,
        ShelfEntryResponse shelfEntry,
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
