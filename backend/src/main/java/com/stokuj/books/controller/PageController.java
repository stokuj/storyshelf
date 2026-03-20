package com.stokuj.books.controller;

import com.stokuj.books.dto.request.UserBookRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.model.enums.ReadingStatus;
import com.stokuj.books.model.entity.User;
import com.stokuj.books.repository.UserRepository;
import com.stokuj.books.service.BookService;
import com.stokuj.books.service.BookChapterService;
import com.stokuj.books.service.UserBookService;
import com.stokuj.books.service.UserProfileService;
import com.stokuj.books.dto.request.UserProfileUpdateRequest;
import com.stokuj.books.dto.response.UserSettingsResponse;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import jakarta.validation.Valid;
import org.springframework.security.core.Authentication;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.validation.annotation.Validated;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@Validated
public class PageController {

    private final BookService bookService;
    private final BookChapterService bookChapterService;
    private final UserBookService userBookService;
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserProfileService userProfileService;

    public PageController(BookService bookService,
                          BookChapterService bookChapterService,
                          UserBookService userBookService,
                          UserRepository userRepository,
                          PasswordEncoder passwordEncoder,
                          UserProfileService userProfileService) {
        this.bookService = bookService;
        this.bookChapterService = bookChapterService;
        this.userBookService = userBookService;
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.userProfileService = userProfileService;
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
    public String settings(Model model, Authentication authentication) {
        UserSettingsResponse settings = userProfileService.toSettingsResponse(
                userProfileService.findByEmail(authentication.getName())
        );
        if (!model.containsAttribute("profileForm")) {
            model.addAttribute("profileForm", new UserProfileUpdateRequest(
                    settings.username(),
                    settings.bio(),
                    settings.avatarUrl()
            ));
        }
        model.addAttribute("settings", settings);
        return "settings";
    }

    @PostMapping("/settings")
    public String updateSettings(@Valid @ModelAttribute("profileForm") UserProfileUpdateRequest request,
                                 org.springframework.validation.BindingResult bindingResult,
                                 Authentication authentication,
                                 RedirectAttributes redirectAttributes,
                                 Model model) {
        if (bindingResult.hasErrors()) {
            UserSettingsResponse settings = userProfileService.toSettingsResponse(
                    userProfileService.findByEmail(authentication.getName())
            );
            model.addAttribute("settings", settings);
            return "settings";
        }

        UserSettingsResponse updated = userProfileService.updateProfile(
                userProfileService.findByEmail(authentication.getName()),
                request
        );
        redirectAttributes.addFlashAttribute("settingsMsg", "Zapisano zmiany profilu.");
        return "redirect:/settings";
    }

    @PostMapping("/settings/visibility")
    public String updateVisibility(@RequestParam("profilePublic") boolean profilePublic,
                                   Authentication authentication,
                                   RedirectAttributes redirectAttributes) {
        userProfileService.updateVisibility(
                userProfileService.findByEmail(authentication.getName()),
                profilePublic
        );
        redirectAttributes.addFlashAttribute("settingsMsg", "Zmieniono widoczność profilu.");
        return "redirect:/settings";
    }

    @GetMapping("/profile/{username}")
    public String profile(@PathVariable String username,
                          Authentication authentication,
                          Model model) {
        User user = userProfileService.findByUsername(username);
        boolean isOwner = hasAuthenticatedUser(authentication)
                && authentication.getName().equalsIgnoreCase(user.getEmail());

        if (!user.isProfilePublic() && !isOwner) {
            model.addAttribute("status", 403);
            model.addAttribute("error", "Forbidden");
            model.addAttribute("message", "Ten profil jest prywatny.");
            return "error";
        }

        model.addAttribute("profile", userProfileService.toPublicResponse(user));
        model.addAttribute("isOwner", isOwner);
        return "profile";
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
    public String register(@RequestParam @NotBlank
                           String username,
                           @RequestParam @Email @NotBlank String email,
                           @RequestParam @NotBlank @Size(min = 6) String password,
                           RedirectAttributes redirectAttributes) {
        if (username == null || !username.matches("[a-z]{3,30}")) {
            redirectAttributes.addFlashAttribute("registerError", "Username musi mieć 3-30 małych liter (a-z).");
            return "redirect:/register";
        }
        if (userRepository.findByEmail(email).isPresent()) {
            redirectAttributes.addFlashAttribute("registerError", "Użytkownik z tym adresem email już istnieje.");
            return "redirect:/register";
        }
        if (userRepository.existsByUsername(username)) {
            redirectAttributes.addFlashAttribute("registerError", "Username jest już zajęty.");
            return "redirect:/register";
        }

        User user = new User();
        user.setEmail(email);
        user.setPassword(passwordEncoder.encode(password));
        user.setRole(com.stokuj.books.model.enums.Role.USER);
        user.setUsername(username);
        userRepository.save(user);

        return "redirect:/login?registered";
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

    // -------------------------------------------------------------------------
    // Upload treści książki (HTML formularz)
    // -------------------------------------------------------------------------

    @PostMapping("/book/{id}/content")
    public String uploadBookContent(@PathVariable Long id,
                                    @RequestParam("file") MultipartFile file,
                                    RedirectAttributes redirectAttributes) {
        if (file == null || file.isEmpty()) {
            redirectAttributes.addFlashAttribute("contentMsg", "Wybierz plik .txt przed wysłaniem.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        String content;
        try {
            content = new String(file.getBytes(), StandardCharsets.UTF_8).strip();
        } catch (IOException e) {
            redirectAttributes.addFlashAttribute("contentMsg", "Nie udało się odczytać pliku.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        if (content.isBlank()) {
            redirectAttributes.addFlashAttribute("contentMsg", "Plik jest pusty.");
            redirectAttributes.addFlashAttribute("contentMsgType", "error");
            return "redirect:/book/" + id;
        }

        int chaptersCount = bookChapterService.loadContent(id, content);
        redirectAttributes.addFlashAttribute("contentMsg", "Treść wgrana. Rozdziałów: " + chaptersCount + ".");
        redirectAttributes.addFlashAttribute("contentMsgType", "success");
        return "redirect:/book/" + id;
    }

}
