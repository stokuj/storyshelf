package com.stokuj.books.controller.api.admin;

import com.stokuj.books.service.ReviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/admin/reviews")
@Tag(name = "Reviews", description = "Admin endpoints for Review management")
public class AdminReviewController {

    private final ReviewService reviewService;

    public AdminReviewController(ReviewService reviewService) {
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
