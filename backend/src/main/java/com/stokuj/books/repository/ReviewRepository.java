package com.stokuj.books.repository;

import com.stokuj.books.model.entity.Review;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ReviewRepository extends JpaRepository<Review, Long> {
    Optional<Review> findByBookIdAndUserId(Long bookId, Long userId);

    List<Review> findAllByBookIdOrderByCreatedAtDesc(Long bookId);

    List<Review> findAllByOrderByCreatedAtDesc();

    long countByBookId(Long bookId);

    @Query("select avg(r.rating) from Review r where r.book.id = :bookId")
    Double findAverageRating(@Param("bookId") Long bookId);
}
