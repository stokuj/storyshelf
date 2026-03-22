package com.stokuj.books.controller.web;

import com.stokuj.books.domain.entity.User;
import com.stokuj.books.repository.UserRepository;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@Validated
public class AuthWebController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthWebController(UserRepository userRepository,
                             PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

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

    @GetMapping("/register")
    public String registerForm() {
        return "register";
    }

    @PostMapping("/register")
    public String register(@RequestParam @NotBlank String username,
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
        user.setRole(com.stokuj.books.domain.enums.Role.USER);
        user.setUsername(username);
        userRepository.save(user);

        return "redirect:/login?registered";
    }
}
