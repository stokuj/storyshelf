package com.stokuj.books.book.book.dto;

import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.book.chapter.dto.ChapterResponse;
import com.stokuj.books.book.character.relation.dto.CharacterRelationResponse;
import com.stokuj.books.book.character.core.dto.CharacterResponse;
import com.stokuj.books.review.dto.ReviewResponse;

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
