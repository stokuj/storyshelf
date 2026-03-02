package com.stokuj.books.service;

import com.stokuj.books.dto.AuthRequest;
import com.stokuj.books.dto.AuthResponse;
import com.stokuj.books.model.User;
import com.stokuj.books.repository.UserRepository;
import com.stokuj.books.security.JwtService;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthResponse register(AuthRequest request) {
        // sprawdź czy użytkownik z tym emailem już istnieje
        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new RuntimeException("Użytkownik z tym emailem już istnieje");
        }

        // stwórz nowego użytkownika
        User user = new User();
        user.setEmail(request.getEmail());
        // hashuj hasło — nigdy nie zapisujemy plaintext
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setRole("ROLE_USER");

        userRepository.save(user);

        // wygeneruj token i zwróć
        String token = jwtService.generateToken(user.getEmail());
        return new AuthResponse(token);
    }

    public AuthResponse login(AuthRequest request) {
        // znajdź użytkownika po emailu
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new RuntimeException("Nieprawidłowy email lub hasło"));

        // sprawdź czy hasło się zgadza
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new RuntimeException("Nieprawidłowy email lub hasło");
        }

        // wygeneruj token i zwróć
        String token = jwtService.generateToken(user.getEmail());
        return new AuthResponse(token);
    }
}