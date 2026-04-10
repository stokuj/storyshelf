package com.stokuj.books.review;

import com.stokuj.books.book.Book;
import com.stokuj.books.review.Review;
import com.stokuj.books.user.User;
import com.stokuj.books.review.ReviewRequest;
import com.stokuj.books.review.ReviewResponse;
import com.stokuj.books.core.ConflictException;
import com.stokuj.books.core.ResourceNotFoundException;
import com.stokuj.books.book.BookRepository;
import com.stokuj.books.review.ReviewRepository;
import com.stokuj.books.user.UserRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReviewService {

    private final ReviewRepository reviewRepository;
    private final BookRepository bookRepository;
    private final UserRepository userRepository;

    public ReviewService(ReviewRepository reviewRepository,
                         BookRepository bookRepository,
                         UserRepository userRepository) {
        this.reviewRepository = reviewRepository;
        this.bookRepository = bookRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public ReviewResponse addReview(Long bookId, String userEmail, ReviewRequest request) {
        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        if (reviewRepository.findByBookIdAndUserId(bookId, user.getId()).isPresent()) {
            throw new ConflictException("Recenzja już istnieje");
        }

        Review review = new Review();
        review.setBook(book);
        review.setUser(user);
        review.setRating(request.getRating());
        review.setContent(normalizeContent(request.getContent()));
        Review saved = reviewRepository.save(review);

        updateBookRatings(bookId, book);

        return toResponse(saved);
    }

    @Transactional
    public void deleteReview(Long reviewId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new ResourceNotFoundException("Review not found"));
        Long bookId = review.getBook().getId();

        reviewRepository.delete(review);

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));
        updateBookRatings(bookId, book);
    }

    public List<ReviewResponse> getReviewsForBook(Long bookId) {
        return reviewRepository.findAllByBookIdOrderByCreatedAtDesc(bookId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    public List<ReviewResponse> getAllReviews() {
        return reviewRepository.findAllByOrderByCreatedAtDesc()
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private void updateBookRatings(Long bookId, Book book) {
        long count = reviewRepository.countByBookId(bookId);
        Double average = reviewRepository.findAverageRating(bookId);
        book.setRatingsCount((int) count);
        book.setRating(average != null ? average : 0.0);
        bookRepository.save(book);
    }

    private ReviewResponse toResponse(Review review) {
        return new ReviewResponse(
                review.getId(),
                review.getUser().getUsername(),
                review.getRating(),
                review.getContent(),
                review.getCreatedAt(),
                review.getBook().getTitle(),
                review.getBook().getId()
        );
    }

    private String normalizeContent(String content) {
        if (content == null) {
            return null;
        }
        String trimmed = content.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
