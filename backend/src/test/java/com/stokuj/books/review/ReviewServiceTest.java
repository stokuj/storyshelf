package com.stokuj.books.review;

import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.review.dto.ReviewRequest;
import com.stokuj.books.review.dto.ReviewResponse;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ReviewServiceTest {

    @Mock
    ReviewRepository reviewRepository;

    @Mock
    BookRepository bookRepository;

    @Mock
    UserRepository userRepository;

    @InjectMocks
    ReviewService reviewService;

    @Nested
    class AddReview {

        @Test
        void shouldAddReviewSuccessfully() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            ReviewRequest request = new ReviewRequest(5, " Great book with many details ");

            given(bookRepository.findById(1L)).willReturn(Optional.of(book));
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(reviewRepository.findByBookIdAndUserId(1L, 10L)).willReturn(Optional.empty());
            given(reviewRepository.save(org.mockito.ArgumentMatchers.any(Review.class)))
                    .willAnswer(invocation -> {
                        Review review = invocation.getArgument(0);
                        setField(review, "id", 100L);
                        setField(review, "createdAt", Instant.parse("2024-01-01T00:00:00Z"));
                        return review;
                    });
            given(reviewRepository.countByBookId(1L)).willReturn(1L);
            given(reviewRepository.findAverageRating(1L)).willReturn(5.0);
            given(bookRepository.save(book)).willReturn(book);

            ReviewResponse response = reviewService.addReview(1L, "john@example.com", request);

            ArgumentCaptor<Review> captor = ArgumentCaptor.forClass(Review.class);
            verify(reviewRepository).save(captor.capture());
            Review saved = captor.getValue();
            assertThat(getField(saved, "rating")).isEqualTo(5);
            assertThat(getField(saved, "content")).isEqualTo("Great book with many details");
            assertThat(getField(saved, "book")).isEqualTo(book);
            assertThat(getField(saved, "user")).isEqualTo(user);
            assertThat(response.id()).isEqualTo(100L);
            assertThat(response.username()).isEqualTo("john");
            assertThat(response.bookTitle()).isEqualTo("Dune");

            assertThat(getField(book, "ratingsCount")).isEqualTo(1);
            assertThat(getField(book, "rating")).isEqualTo(5.0);
        }

        @Test
        void shouldThrowWhenBookNotFound() {
            given(bookRepository.findById(1L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> reviewService.addReview(1L, "john@example.com", new ReviewRequest(5, "Great book text")))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }

        @Test
        void shouldThrowWhenUserNotFound() {
            given(bookRepository.findById(1L)).willReturn(Optional.of(book(1L, "Dune")));
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.empty());

            assertThatThrownBy(() -> reviewService.addReview(1L, "john@example.com", new ReviewRequest(5, "Great book text")))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }

        @Test
        void shouldThrowWhenReviewAlreadyExists() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            given(bookRepository.findById(1L)).willReturn(Optional.of(book));
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(reviewRepository.findByBookIdAndUserId(1L, 10L)).willReturn(Optional.of(new Review()));

            assertThatThrownBy(() -> reviewService.addReview(1L, "john@example.com", new ReviewRequest(5, "Great book text")))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("Review already exists");
        }

        @Test
        void shouldStoreNullContentWhenOnlyWhitespaceProvided() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            given(bookRepository.findById(1L)).willReturn(Optional.of(book));
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(reviewRepository.findByBookIdAndUserId(1L, 10L)).willReturn(Optional.empty());
            given(reviewRepository.save(org.mockito.ArgumentMatchers.any(Review.class)))
                    .willAnswer(invocation -> invocation.getArgument(0));
            given(reviewRepository.countByBookId(1L)).willReturn(1L);
            given(reviewRepository.findAverageRating(1L)).willReturn(4.0);

            reviewService.addReview(1L, "john@example.com", new ReviewRequest(4, "    "));

            ArgumentCaptor<Review> captor = ArgumentCaptor.forClass(Review.class);
            verify(reviewRepository).save(captor.capture());
            assertThat(getField(captor.getValue(), "content")).isNull();
        }
    }

    @Nested
    class DeleteReview {

        @Test
        void shouldDeleteReviewAndUpdateBookRatings() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            Review review = review(100L, book, user, 5, "Great");
            given(reviewRepository.findById(100L)).willReturn(Optional.of(review));
            given(bookRepository.findById(1L)).willReturn(Optional.of(book));
            given(reviewRepository.countByBookId(1L)).willReturn(0L);
            given(reviewRepository.findAverageRating(1L)).willReturn(null);

            reviewService.deleteReview(100L);

            verify(reviewRepository).delete(review);
            verify(bookRepository).save(book);
            assertThat(getField(book, "ratingsCount")).isEqualTo(0);
            assertThat(getField(book, "rating")).isEqualTo(0.0);
        }

        @Test
        void shouldThrowWhenReviewNotFound() {
            given(reviewRepository.findById(100L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> reviewService.deleteReview(100L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Review not found");
        }

        @Test
        void shouldThrowWhenBookMissingAfterDelete() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            Review review = review(100L, book, user, 5, "Great");
            given(reviewRepository.findById(100L)).willReturn(Optional.of(review));
            given(bookRepository.findById(1L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> reviewService.deleteReview(100L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }
    }

    @Nested
    class Querying {

        @Test
        void shouldReturnMappedReviewsForBook() {
            Book book = book(1L, "Dune");
            User user = user(10L, "john", "john@example.com");
            Review review = review(100L, book, user, 5, "Great");
            setField(review, "createdAt", Instant.parse("2024-01-01T00:00:00Z"));
            given(reviewRepository.findAllByBookIdOrderByCreatedAtDesc(1L)).willReturn(List.of(review));

            List<ReviewResponse> result = reviewService.getReviewsForBook(1L);

            assertThat(result).hasSize(1);
            assertThat(result.getFirst().id()).isEqualTo(100L);
            assertThat(result.getFirst().username()).isEqualTo("john");
            assertThat(result.getFirst().bookId()).isEqualTo(1L);
        }

        @Test
        void shouldReturnMappedAllReviews() {
            Book book = book(2L, "Foundation");
            User user = user(11L, "anna", "anna@example.com");
            Review review = review(101L, book, user, 4, "Very good");
            given(reviewRepository.findAllByOrderByCreatedAtDesc()).willReturn(List.of(review));

            List<ReviewResponse> result = reviewService.getAllReviews();

            assertThat(result).hasSize(1);
            assertThat(result.getFirst().id()).isEqualTo(101L);
            assertThat(result.getFirst().bookTitle()).isEqualTo("Foundation");
        }
    }

    private Book book(Long id, String title) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "title", title);
        setField(book, "bookAuthors", new java.util.ArrayList<>());
        setField(book, "bookTags", new java.util.ArrayList<>());
        return book;
    }

    private User user(Long id, String username, String email) {
        User user = new User();
        setField(user, "id", id);
        setField(user, "username", username);
        setField(user, "email", email);
        return user;
    }

    private Review review(Long id, Book book, User user, int rating, String content) {
        Review review = new Review();
        setField(review, "id", id);
        setField(review, "book", book);
        setField(review, "user", user);
        setField(review, "rating", rating);
        setField(review, "content", content);
        setField(review, "createdAt", Instant.parse("2024-01-01T00:00:00Z"));
        return review;
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

    private Object getField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
