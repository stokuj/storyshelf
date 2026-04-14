package com.stokuj.books.book.book;

import com.stokuj.books.book.book.dto.BookDetailResponse;
import com.stokuj.books.book.book.dto.BookResponse;
import com.stokuj.books.book.chapter.BookChapterService;
import com.stokuj.books.book.chapter.dto.ChapterResponse;
import com.stokuj.books.book.character.aggregation.BookCharacter;
import com.stokuj.books.book.character.aggregation.BookCharacterRepository;
import com.stokuj.books.book.character.core.StoryCharacter;
import com.stokuj.books.book.character.relation.StoryCharacterRelation;
import com.stokuj.books.book.character.relation.StoryCharacterRelationRepository;
import com.stokuj.books.bookshelf.ShelfEntryService;
import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.review.ReviewService;
import com.stokuj.books.review.dto.ReviewResponse;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class BookDetailServiceTest {

    @Mock
    BookService bookService;

    @Mock
    BookChapterService bookChapterService;

    @Mock
    BookCharacterRepository bookCharacterRepository;

    @Mock
    StoryCharacterRelationRepository characterRelationRepository;

    @Mock
    ReviewService reviewService;

    @Mock
    ShelfEntryService shelfEntryService;

    @InjectMocks
    BookDetailService bookDetailService;

    @Nested
    class Aggregation {

        @Test
        void shouldReturnAggregatedDetailsForAnonymousUser() {
            Long bookId = 1L;
            Book book = book(bookId, 5, 3);
            given(bookService.getEntityById(bookId)).willReturn(book);
            given(bookService.toDto(book)).willReturn(bookResponse(bookId, "Dune"));
            given(bookChapterService.getChapters(bookId)).willReturn(List.of(chapter(10L, bookId, 1)));
            given(bookCharacterRepository.findAllByBookIdWithCharacter(bookId)).willReturn(List.of(bookCharacter(11L, "Paul", 12, "MAIN")));
            given(characterRelationRepository.findAllByBookId(bookId)).willReturn(List.of(relation(20L, "Paul", "Chani", "ALLY")));
            given(reviewService.getReviewsForBook(bookId)).willReturn(List.of(review(30L, "john", bookId)));

            BookDetailResponse result = bookDetailService.getById(bookId, null);

            assertThat(result.book().title()).isEqualTo("Dune");
            assertThat(result.analysisStatus().chaptersCount()).isEqualTo(5);
            assertThat(result.analysisStatus().nerCompletedCount()).isEqualTo(3);
            assertThat(result.analysisStatus().analysisFinished()).isFalse();
            assertThat(result.shelfEntry()).isNull();
            assertThat(result.chapters()).hasSize(1);
            assertThat(result.characters()).hasSize(1);
            assertThat(result.relations()).hasSize(1);
            assertThat(result.reviews()).hasSize(1);
        }

        @Test
        void shouldReturnAggregatedDetailsForAuthenticatedUserWithShelfEntry() {
            Long bookId = 2L;
            String email = "john@example.com";
            Book book = book(bookId, 2, 2);
            ShelfEntryResponse shelf = new ShelfEntryResponse(
                    new ShelfEntryResponse.BookSummary(bookId, "Dune", "Frank Herbert"),
                    com.stokuj.books.bookshelf.ReadingStatus.READING,
                    Instant.parse("2024-01-01T00:00:00Z")
            );

            given(bookService.getEntityById(bookId)).willReturn(book);
            given(bookService.toDto(book)).willReturn(bookResponse(bookId, "Dune"));
            given(bookChapterService.getChapters(bookId)).willReturn(List.of());
            given(bookCharacterRepository.findAllByBookIdWithCharacter(bookId)).willReturn(List.of());
            given(characterRelationRepository.findAllByBookId(bookId)).willReturn(List.of());
            given(reviewService.getReviewsForBook(bookId)).willReturn(List.of());
            given(shelfEntryService.findByUserAndBook(email, bookId)).willReturn(Optional.of(shelf));

            BookDetailResponse result = bookDetailService.getById(bookId, email);

            assertThat(result.analysisStatus().analysisFinished()).isTrue();
            assertThat(result.shelfEntry()).isEqualTo(shelf);
            verify(shelfEntryService).findByUserAndBook(email, bookId);
        }

        @Test
        void shouldMarkAnalysisNotFinishedWhenNoChapters() {
            Long bookId = 3L;
            Book book = book(bookId, 0, 0);
            given(bookService.getEntityById(bookId)).willReturn(book);
            given(bookService.toDto(book)).willReturn(bookResponse(bookId, "Dune"));
            given(bookChapterService.getChapters(bookId)).willReturn(List.of());
            given(bookCharacterRepository.findAllByBookIdWithCharacter(bookId)).willReturn(List.of());
            given(characterRelationRepository.findAllByBookId(bookId)).willReturn(List.of());
            given(reviewService.getReviewsForBook(bookId)).willReturn(List.of());

            BookDetailResponse result = bookDetailService.getById(bookId, null);

            assertThat(result.analysisStatus().analysisFinished()).isFalse();
        }
    }

    @Test
    void shouldPropagateWhenBookNotFound() {
        given(bookService.getEntityById(404L)).willThrow(new ResourceNotFoundException("Book not found"));

        assertThatThrownBy(() -> bookDetailService.getById(404L, null))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessage("Book not found");
    }

    private Book book(Long id, int chaptersCount, int nerCompleted) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "chaptersCount", chaptersCount);
        setField(book, "nerCompletedCount", nerCompleted);
        return book;
    }

    private BookResponse bookResponse(Long id, String title) {
        return new BookResponse(id, title, "Author", 2000, null, null, 300, Set.of("Fiction"), List.of("classic"), 4.0, 10);
    }

    private ChapterResponse chapter(Long id, Long bookId, int number) {
        return new ChapterResponse(id, bookId, number, "Chapter " + number, false, 100, 90, 20, 25);
    }

    private BookCharacter bookCharacter(Long characterId, String name, int mentionCount, String role) {
        StoryCharacter character = new StoryCharacter();
        setField(character, "id", characterId);
        setField(character, "name", name);

        BookCharacter bc = new BookCharacter();
        setField(bc, "character", character);
        setField(bc, "mentionCount", mentionCount);
        setField(bc, "role", role);
        return bc;
    }

    private StoryCharacterRelation relation(Long id, String sourceName, String targetName, String relationName) {
        StoryCharacter source = new StoryCharacter();
        setField(source, "name", sourceName);
        StoryCharacter target = new StoryCharacter();
        setField(target, "name", targetName);

        StoryCharacterRelation relation = new StoryCharacterRelation();
        setField(relation, "id", id);
        setField(relation, "source", source);
        setField(relation, "target", target);
        setField(relation, "relation", relationName);
        setField(relation, "evidence", "evidence");
        setField(relation, "confidence", 0.9d);
        return relation;
    }

    private ReviewResponse review(Long id, String username, Long bookId) {
        return new ReviewResponse(id, username, 5, "Great book", Instant.parse("2024-01-01T00:00:00Z"), "Title", bookId);
    }

    private void setField(Object target, String fieldName, Object value) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
