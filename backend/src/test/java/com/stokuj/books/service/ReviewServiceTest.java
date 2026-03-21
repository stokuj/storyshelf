package com.stokuj.books.service;

import com.stokuj.books.dto.request.ReviewRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.entity.Book;
import com.stokuj.books.model.entity.Review;
import com.stokuj.books.model.entity.User;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.ReviewRepository;
import com.stokuj.books.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ReviewServiceTest {

    @Mock
    private ReviewRepository reviewRepository;

    @Mock
    private BookRepository bookRepository;

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private ReviewService reviewService;

    private User testUser;
    private Book testBook;

    @BeforeEach
    void setUp() {
        testUser = new User();
        testUser.setId(1L);
        testUser.setEmail("test@example.com");

        testBook = new Book();
        testBook.setId(10L);
        testBook.setRating(0.0);
        testBook.setRatingsCount(0);
    }

    @Test
    void addReview_throwsConflictException_whenReviewAlreadyExists() {
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(bookRepository.findById(10L)).thenReturn(Optional.of(testBook));
        when(reviewRepository.existsByBookIdAndUserId(10L, 1L)).thenReturn(true);

        ReviewRequest request = new ReviewRequest(5, "Great book");

        assertThatThrownBy(() -> reviewService.addReview("test@example.com", 10L, request))
                .isInstanceOf(ConflictException.class)
                .hasMessageContaining("Dodałeś/aś");
                
        verify(reviewRepository, never()).save(any(Review.class));
        verify(bookRepository, never()).save(any(Book.class));
    }

    @Test
    void addReview_updatesAverageRating_whenSuccess() {
        when(userRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testUser));
        when(bookRepository.findById(10L)).thenReturn(Optional.of(testBook));
        when(reviewRepository.existsByBookIdAndUserId(10L, 1L)).thenReturn(false);

        // Previous state: Rating = 0.0, Count = 0
        ReviewRequest request = new ReviewRequest(4, "Good read");
        
        Review savedReview = new Review();
        savedReview.setId(100L);
        savedReview.setRating(4);
        savedReview.setContent("Good read");
        savedReview.setBook(testBook);
        savedReview.setUser(testUser);
        
        when(reviewRepository.save(any(Review.class))).thenReturn(savedReview);

        reviewService.addReview("test@example.com", 10L, request);

        verify(reviewRepository).save(any(Review.class));
        verify(bookRepository).save(testBook);

        assertThat(testBook.getRatingsCount()).isEqualTo(1);
        assertThat(testBook.getRating()).isEqualTo(4.0);
    }

    @Test
    void deleteReview_updatesAverageRating_whenSuccess() {
        Review review = new Review();
        review.setId(100L);
        review.setRating(5);
        review.setUser(testUser);
        review.setBook(testBook);

        testBook.setRating(5.0);
        testBook.setRatingsCount(1);

        when(reviewRepository.findById(100L)).thenReturn(Optional.of(review));

        reviewService.deleteReview(100L);

        verify(reviewRepository).delete(review);
        verify(bookRepository).save(testBook);

        assertThat(testBook.getRatingsCount()).isEqualTo(0);
        assertThat(testBook.getRating()).isEqualTo(0.0);
    }
}
