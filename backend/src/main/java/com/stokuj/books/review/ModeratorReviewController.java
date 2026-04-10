package com.stokuj.books.review;

import com.stokuj.books.review.ReviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/moderator/reviews")
@Tag(name = "Moderator - Reviews", description = "Moderator endpoints for review moderation")
public class ModeratorReviewController {

    private final ReviewService reviewService;

    public ModeratorReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('MODERATOR')")
    @Operation(summary = "Delete a review")
    public ResponseEntity<Void> deleteReview(@PathVariable Long id) {
        reviewService.deleteReview(id);
        return ResponseEntity.noContent().build();
    }
}
