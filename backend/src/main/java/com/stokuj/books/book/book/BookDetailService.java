package com.stokuj.books.book.book;

import com.stokuj.books.book.book.dto.BookDetailResponse;
import com.stokuj.books.book.book.dto.BookResponse;
import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.book.chapter.dto.ChapterResponse;
import com.stokuj.books.book.character.relation.dto.CharacterRelationResponse;
import com.stokuj.books.book.character.core.dto.CharacterResponse;
import com.stokuj.books.review.dto.ReviewResponse;
import com.stokuj.books.review.ReviewService;
import com.stokuj.books.bookshelf.ShelfEntryService;
import com.stokuj.books.book.character.aggregation.BookCharacterRepository;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import org.springframework.stereotype.Service;

import java.util.List;

import com.stokuj.books.book.chapter.BookChapterService;
@Service
public class BookDetailService {

    private final BookService bookService;
    private final BookChapterService bookChapterService;
    private final BookCharacterRepository bookCharacterRepository;
    private final StoryCharacterRelationRepository characterRelationRepository;
    private final ReviewService reviewService;
    private final ShelfEntryService userBookService;

    public BookDetailService(BookService bookService,
                             BookChapterService bookChapterService,
                             BookCharacterRepository bookCharacterRepository,
                             StoryCharacterRelationRepository characterRelationRepository,
                             ReviewService reviewService,
                             ShelfEntryService userBookService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
        this.reviewService = reviewService;
        this.userBookService = userBookService;
    }

    public BookDetailResponse getById(Long id, String email) {
        Book book = bookService.getEntityById(id);

        BookResponse bookResponse = bookService.toDto(book);
        BookDetailResponse.AnalysisStatusResponse analysisStatus =
                new BookDetailResponse.AnalysisStatusResponse(
                        book.getChaptersCount(),
                        book.getNerCompletedCount(),
                        book.getChaptersCount() > 0 && book.getNerCompletedCount() >= book.getChaptersCount()
                );
        ShelfEntryResponse shelfEntry = email == null
                ? null
                : userBookService.findByUserAndBook(email, id).orElse(null);

        List<ChapterResponse> chapters = bookChapterService.getChapters(id);
        List<CharacterResponse> characters = bookCharacterRepository.findAllByBookIdWithCharacter(id).stream()
                .map(bookCharacter -> new CharacterResponse(
                        bookCharacter.getCharacter().getId(),
                        bookCharacter.getCharacter().getName(),
                        bookCharacter.getMentionCount(),
                        bookCharacter.getRole()
                ))
                .toList();
        List<CharacterRelationResponse> relations = characterRelationRepository.findAllByBookId(id).stream()
                .map(relation -> new CharacterRelationResponse(
                        relation.getId(),
                        relation.getSource().getName(),
                        relation.getTarget().getName(),
                        relation.getRelation(),
                        relation.getEvidence(),
                        relation.getConfidence()
                ))
                .toList();
        List<ReviewResponse> reviews = reviewService.getReviewsForBook(id);

        return new BookDetailResponse(bookResponse, analysisStatus, shelfEntry, chapters, characters, relations, reviews);
    }
}
