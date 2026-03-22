package com.stokuj.books.controller.api;

import com.stokuj.books.dto.review.ReviewRequest;
import com.stokuj.books.dto.review.ReviewResponse;
import com.stokuj.books.service.ReviewService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @GetMapping("/books/{id}/reviews")
    public ResponseEntity<List<ReviewResponse>> getReviews(@PathVariable Long id) {
        return ResponseEntity.ok(reviewService.getReviewsForBook(id));
    }

    @PostMapping("/books/{id}/reviews")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<ReviewResponse> addReview(@PathVariable Long id,
                                                    @RequestBody ReviewRequest request,
                                                    Authentication authentication) {
        return ResponseEntity.status(201)
                .body(reviewService.addReview(id, authentication.getName(), request));
    }

    @DeleteMapping("/reviews/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    public ResponseEntity<Void> deleteReview(@PathVariable Long id) {
        reviewService.deleteReview(id);
        return ResponseEntity.noContent().build();
    }
}