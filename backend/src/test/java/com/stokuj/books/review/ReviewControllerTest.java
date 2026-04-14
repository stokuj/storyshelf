package com.stokuj.books.review;

import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.review.dto.ReviewRequest;
import com.stokuj.books.review.dto.ReviewResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;

import java.time.Instant;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ReviewControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    ReviewService reviewService;

    @Mock
    Authentication authentication;

    @InjectMocks
    ReviewController reviewController;

    @BeforeAll
    static void setUpValidator() {
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    @Nested
    class GetReviews {

        @Test
        void shouldReturnReviewsForBook() {
            List<ReviewResponse> reviews = List.of(
                    response(1L, "john", 5, "Great book with a great story", 10L),
                    response(2L, "anna", 4, "Very good read overall", 10L)
            );
            given(reviewService.getReviewsForBook(10L)).willReturn(reviews);

            ResponseEntity<List<ReviewResponse>> result = reviewController.getReviews(10L);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).hasSize(2);
            assertThat(result.getBody().get(0).username()).isEqualTo("john");
            assertThat(result.getBody().get(1).username()).isEqualTo("anna");
        }

        @Test
        void shouldReturnEmptyReviewsList() {
            given(reviewService.getReviewsForBook(99L)).willReturn(List.of());

            ResponseEntity<List<ReviewResponse>> result = reviewController.getReviews(99L);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEmpty();
        }
    }

    @Nested
    class AddReview {

        @Test
        void shouldAddReviewAndReturnCreated() {
            ReviewRequest request = new ReviewRequest(5, "Great book with a great story");
            ReviewResponse expected = response(3L, "john", 5, "Great book with a great story", 10L);
            given(authentication.getName()).willReturn("john@example.com");
            given(reviewService.addReview(10L, "john@example.com", request)).willReturn(expected);

            ResponseEntity<ReviewResponse> result = reviewController.addReview(10L, request, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(result.getBody()).isEqualTo(expected);
        }

        @Test
        void shouldPropagateConflictWhenReviewExists() {
            ReviewRequest request = new ReviewRequest(5, "Great book with a great story");
            given(authentication.getName()).willReturn("john@example.com");
            given(reviewService.addReview(10L, "john@example.com", request))
                    .willThrow(new ConflictException("Review already exists"));

            assertThatThrownBy(() -> reviewController.addReview(10L, request, authentication))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("Review already exists");
        }

        @Test
        void shouldPropagateNotFoundWhenBookOrUserMissing() {
            ReviewRequest request = new ReviewRequest(5, "Great book with a great story");
            given(authentication.getName()).willReturn("john@example.com");
            given(reviewService.addReview(404L, "john@example.com", request))
                    .willThrow(new ResourceNotFoundException("Book not found"));

            assertThatThrownBy(() -> reviewController.addReview(404L, request, authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }

        @Test
        void shouldHaveValidationViolationsForInvalidReviewRequest() {
            ReviewRequest invalid = new ReviewRequest(0, "short");

            Set<ConstraintViolation<ReviewRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("rating"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("content"));
        }
    }

    @Nested
    class DeleteReview {

        @Test
        void shouldDeleteReviewAndReturnNoContent() {
            ResponseEntity<Void> result = reviewController.deleteReview(7L);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
            verify(reviewService).deleteReview(7L);
        }

        @Test
        void shouldPropagateNotFoundWhenDeletingMissingReview() {
            org.mockito.Mockito.doThrow(new ResourceNotFoundException("Review not found"))
                    .when(reviewService)
                    .deleteReview(404L);

            assertThatThrownBy(() -> reviewController.deleteReview(404L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Review not found");
        }
    }

    private ReviewResponse response(Long id, String username, int rating, String content, Long bookId) {
        return new ReviewResponse(
                id,
                username,
                rating,
                content,
                Instant.now(),
                "Book title",
                bookId
        );
    }
}
