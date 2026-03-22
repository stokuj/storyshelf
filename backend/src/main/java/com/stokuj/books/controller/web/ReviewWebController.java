package com.stokuj.books.controller.web;

import com.stokuj.books.dto.ReviewRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class ReviewWebController {

    private final ReviewService reviewService;

    public ReviewWebController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @PostMapping("/book/{id}/review")
    public String addReview(@PathVariable Long id,
                            @Valid @ModelAttribute("reviewForm") ReviewRequest request,
                            BindingResult bindingResult,
                            Authentication authentication,
                            RedirectAttributes redirectAttributes) {
        if (bindingResult.hasErrors()) {
            redirectAttributes.addFlashAttribute("reviewError", "Sprawdź poprawność recenzji.");
            redirectAttributes.addFlashAttribute("reviewForm", request);
            return "redirect:/book/" + id;
        }

        try {
            reviewService.addReview(id, authentication.getName(), request);
            redirectAttributes.addFlashAttribute("reviewMsg", "Dodano recenzję.");
        } catch (ConflictException e) {
            redirectAttributes.addFlashAttribute("reviewError", "Już dodałeś recenzję do tej książki.");
            redirectAttributes.addFlashAttribute("reviewForm", request);
        }

        return "redirect:/book/" + id;
    }
}
