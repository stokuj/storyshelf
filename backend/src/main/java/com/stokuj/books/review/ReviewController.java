package com.stokuj.books.review;

import com.stokuj.books.review.ReviewRequest;
import com.stokuj.books.review.ReviewResponse;
import com.stokuj.books.review.ReviewService;
import org.springframework.http.ResponseEntity;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api")
@Tag(name = "Reviews", description = "Operations related to book reviews")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @Operation(summary = "Get reviews for a book", description = "Retrieves a list of all reviews for a specific book.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved reviews")
    @GetMapping("/books/{id}/reviews")
    public ResponseEntity<List<ReviewResponse>> getReviews(@PathVariable Long id) {
        return ResponseEntity.ok(reviewService.getReviewsForBook(id));
    }

    @Operation(summary = "Add a review", description = "Allows a user to add a review and rating to a book.")
    @ApiResponse(responseCode = "201", description = "Review added successfully")
    @ApiResponse(responseCode = "401", description = "Unauthorized - authentication required")
    @PostMapping("/books/{id}/reviews")
    @PreAuthorize("hasRole('USER')")
    public ResponseEntity<ReviewResponse> addReview(@PathVariable Long id,
                                                    @Valid @RequestBody ReviewRequest request,
                                                    Authentication authentication) {
        return ResponseEntity.status(201)
                .body(reviewService.addReview(id, authentication.getName(), request));
    }

}
