package com.stokuj.books.controller.web;

import com.stokuj.books.dto.request.UserBookRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.model.enums.ReadingStatus;
import com.stokuj.books.service.UserBookService;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class BookshelfWebController {

    private final UserBookService userBookService;

    public BookshelfWebController(UserBookService userBookService) {
        this.userBookService = userBookService;
    }

    @GetMapping("/bookshelf")
    public String bookshelf(Model model,
                            Authentication authentication) {
        model.addAttribute("entries", userBookService.getMyBooks(authentication.getName()));
        model.addAttribute("statuses", ReadingStatus.values());
        return "bookshelf";
    }

    @PostMapping("/shelf/{bookId}/add")
    public String addToShelf(@PathVariable Long bookId,
                             @RequestParam(required = false) ReadingStatus status,
                             Authentication authentication,
                             RedirectAttributes redirectAttributes) {
        try {
            UserBookRequest req = new UserBookRequest();
            req.setStatus(status != null ? status : ReadingStatus.WANT_TO_READ);
            userBookService.addToShelf(authentication.getName(), bookId, req);
        } catch (ConflictException e) {
            redirectAttributes.addFlashAttribute("shelfMsg", "Książka jest już na półce.");
        }
        return "redirect:/book/" + bookId;
    }

    @PostMapping("/shelf/{bookId}/status")
    public String updateStatus(@PathVariable Long bookId,
                               @RequestParam ReadingStatus status,
                               Authentication authentication,
                               @RequestParam(required = false, defaultValue = "/bookshelf") String returnTo) {
        UserBookRequest req = new UserBookRequest();
        req.setStatus(status);
        userBookService.updateStatus(authentication.getName(), bookId, req);
        return "redirect:" + returnTo;
    }

    @PostMapping("/shelf/{bookId}/remove")
    public String removeFromShelf(@PathVariable Long bookId,
                                  Authentication authentication,
                                  @RequestParam(required = false, defaultValue = "/bookshelf") String returnTo) {
        userBookService.removeFromShelf(authentication.getName(), bookId);
        return "redirect:" + returnTo;
    }
}
