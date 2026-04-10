package com.stokuj.books.service;

import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.dto.book.BookDetailResponse;
import com.stokuj.books.dto.book.BookResponse;
import com.stokuj.books.dto.bookshelf.UserBookResponse;
import com.stokuj.books.dto.chapter.ChapterResponse;
import com.stokuj.books.dto.character.CharacterRelationResponse;
import com.stokuj.books.dto.character.CharacterResponse;
import com.stokuj.books.dto.review.ReviewResponse;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BookDetailService {

    private final BookService bookService;
    private final BookChapterService bookChapterService;
    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final ReviewService reviewService;
    private final UserBookService userBookService;

    public BookDetailService(BookService bookService,
                             BookChapterService bookChapterService,
                             BookCharacterRepository bookCharacterRepository,
                             CharacterRelationRepository characterRelationRepository,
                             ReviewService reviewService,
                             UserBookService userBookService) {
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
        UserBookResponse shelfEntry = email == null
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
