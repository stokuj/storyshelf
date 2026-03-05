package com.stokuj.books.controller;

import com.stokuj.books.dto.UserBookRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.model.ReadingStatus;
import com.stokuj.books.model.User;
import com.stokuj.books.repository.UserRepository;
import com.stokuj.books.service.BookService;
import com.stokuj.books.service.UserBookService;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.security.core.Authentication;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class PageController {

    private final BookService bookService;
    private final UserBookService userBookService;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public PageController(BookService bookService,
                          UserBookService userBookService,
                          UserRepository userRepository,
                          PasswordEncoder passwordEncoder) {
        this.bookService = bookService;
        this.userBookService = userBookService;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    private boolean hasAuthenticatedUser(Authentication authentication) {
        return authentication != null
                && authentication.isAuthenticated()
                && !(authentication instanceof AnonymousAuthenticationToken);
    }

    // -------------------------------------------------------------------------
    // Strona główna / katalog
    // -------------------------------------------------------------------------

    @GetMapping({"/", "/home"})
    public String home(Model model,
                       Authentication authentication) {
        model.addAttribute("books", bookService.getAll());
        if (hasAuthenticatedUser(authentication)) {
            model.addAttribute("shelfEntries",
                    userBookService.getMyBooks(authentication.getName()));
        }
        return "home";
    }

    // -------------------------------------------------------------------------
    // Szczegóły książki
    // -------------------------------------------------------------------------

    @GetMapping("/book/{id}")
    public String bookDetail(@PathVariable Long id,
                             Model model,
                             Authentication authentication) {
        model.addAttribute("book", bookService.getById(id));
        model.addAttribute("statuses", ReadingStatus.values());
        if (hasAuthenticatedUser(authentication)) {
            model.addAttribute("shelfEntry",
                    userBookService.findByUserAndBook(authentication.getName(), id).orElse(null));
        }
        return "book";
    }

    // -------------------------------------------------------------------------
    // Półka użytkownika
    // -------------------------------------------------------------------------

    @GetMapping("/bookshelf")
    public String bookshelf(Model model,
                            Authentication authentication) {
        model.addAttribute("entries", userBookService.getMyBooks(authentication.getName()));
        model.addAttribute("statuses", ReadingStatus.values());
        return "bookshelf";
    }

    // -------------------------------------------------------------------------
    // Ustawienia
    // -------------------------------------------------------------------------

    @GetMapping("/settings")
    public String settings() {
        return "settings";
    }

    // -------------------------------------------------------------------------
    // Logowanie
    // -------------------------------------------------------------------------

    @GetMapping("/login")
    public String login(@RequestParam(required = false) String error,
                        @RequestParam(required = false) String logout,
                        @RequestParam(required = false) String registered,
                        Model model) {
        if (error != null) model.addAttribute("loginError", "Nieprawidłowy email lub hasło.");
        if (logout != null) model.addAttribute("logoutMsg", "Wylogowano pomyślnie.");
        if (registered != null) model.addAttribute("registeredMsg", "Konto zostało utworzone. Możesz się zalogować.");
        return "login";
    }

    // -------------------------------------------------------------------------
    // Rejestracja
    // -------------------------------------------------------------------------

    @GetMapping("/register")
    public String registerForm() {
        return "register";
    }

    @PostMapping("/register")
    public String register(@RequestParam @Email @NotBlank String email,
                           @RequestParam @NotBlank @Size(min = 6) String password,
                           RedirectAttributes redirectAttributes) {
        if (userRepository.findByEmail(email).isPresent()) {
            redirectAttributes.addFlashAttribute("registerError", "Użytkownik z tym adresem email już istnieje.");
            return "redirect:/register";
        }

        User user = new User();
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(password));
        user.setRole("ROLE_USER");
        userRepository.save(user);

        return "redirect:/login?registered";
    }

    // -------------------------------------------------------------------------
    // Akcje półki (POST — formularz HTML)
    // -------------------------------------------------------------------------

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
