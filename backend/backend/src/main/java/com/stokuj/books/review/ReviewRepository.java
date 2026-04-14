package com.stokuj.books.review;

import com.stokuj.books.review.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface ReviewRepository extends JpaRepository<Review, Long> {
    Optional<Review> findByBookIdAndUserId(Long bookId, Long userId);
    List<Review> findAllByBookIdOrderByCreatedAtDesc(Long bookId);
    List<Review> findAllByOrderByCreatedAtDesc();
    long countByBookId(Long bookId);
    @Query("SELECT AVG(r.rating) FROM Review r WHERE r.book.id = :bookId")
    Double findAverageRating(Long bookId);
}
