package com.stokuj.books.controller.web;

import com.stokuj.books.dto.auth.RegisterRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.service.AuthService;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
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

    private final AuthService authService;

    public AuthWebController(AuthService authService) {
        this.authService = authService;
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

        try {
            authService.registerUser(new RegisterRequest(username, email, password));
        } catch (ConflictException ex) {
            redirectAttributes.addFlashAttribute("registerError", ex.getMessage());
            return "redirect:/register";
        }

        return "redirect:/login?registered";
    }
}
