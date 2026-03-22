package com.stokuj.books.controller.web;

import com.stokuj.books.dto.review.ReviewRequest;
import com.stokuj.books.domain.enums.ReadingStatus;
import com.stokuj.books.repository.BookCharacterRepository;
import com.stokuj.books.repository.CharacterRelationRepository;
import com.stokuj.books.service.BookChapterService;
import com.stokuj.books.service.BookService;
import com.stokuj.books.service.ReviewService;
import com.stokuj.books.service.UserBookService;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class HomeController {

    private final BookService bookService;
    private final BookChapterService bookChapterService;
    private final BookCharacterRepository bookCharacterRepository;
    private final CharacterRelationRepository characterRelationRepository;
    private final ReviewService reviewService;
    private final UserBookService userBookService;

    public HomeController(BookService bookService,
                          BookChapterService bookChapterService,
                          BookCharacterRepository bookCharacterRepository,
                          CharacterRelationRepository characterRelationRepository,
                          ReviewService reviewService,
                          UserBookService userBookService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
        this.bookCharacterRepository = bookCharacterRepository;
        this.characterRelationRepository = characterRelationRepository;
        this.reviewService = reviewService;
        this.userBookService = userBookService;
    }

    private boolean hasAuthenticatedUser(Authentication authentication) {
        return authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken);
    }

    @GetMapping({"/", "/home"})
    public String home(Model model,
                       @RequestParam(required = false) String q,
                       Authentication authentication) {
        model.addAttribute("books", bookService.search(q));
        model.addAttribute("q", q);
        if (hasAuthenticatedUser(authentication)) {
            model.addAttribute("shelfEntries",
                    userBookService.getMyBooks(authentication.getName()));
        }
        return "home";
    }

    @GetMapping("/book/{id}")
    public String bookDetail(@PathVariable Long id,
                             Model model,
                             Authentication authentication) {
        model.addAttribute("book", bookService.getById(id));
        model.addAttribute("chapters", bookChapterService.getChapters(id));
        model.addAttribute("bookCharacters", bookCharacterRepository.findAllByBookIdWithCharacter(id));
        model.addAttribute("characterRelations", characterRelationRepository.findAllByBookId(id));
        model.addAttribute("reviews", reviewService.getReviewsForBook(id));
        if (!model.containsAttribute("reviewForm")) {
            model.addAttribute("reviewForm", new ReviewRequest());
        }
        model.addAttribute("statuses", ReadingStatus.values());
        if (hasAuthenticatedUser(authentication)) {
            model.addAttribute("shelfEntry",
                    userBookService.findByUserAndBook(authentication.getName(), id).orElse(null));
        }
        return "book";
    }
}
