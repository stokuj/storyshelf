package com.stokuj.books.service;

import com.stokuj.books.dto.AuthRequest;
import com.stokuj.books.dto.LoginRequest;
import com.stokuj.books.dto.AuthResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.UnauthorizedException;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.repository.UserRepository;
import com.stokuj.books.security.JwtService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtService jwtService) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    public AuthResponse register(AuthRequest request) {
        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new ConflictException("Uzytkownik z tym emailem juz istnieje");
        }
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new ConflictException("Username jest już zajęty");
        }

        User user = new User();
        user.setEmail(request.getEmail());
        user.setPassword(passwordEncoder.encode(request.getPassword()));
        user.setRole(com.stokuj.books.domain.enums.Role.USER);
        user.setUsername(request.getUsername());

        userRepository.save(user);

        String token = jwtService.generateToken(user.getEmail());
        return new AuthResponse(token);
    }

    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new UnauthorizedException("Nieprawidlowy email lub haslo"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            throw new UnauthorizedException("Nieprawidlowy email lub haslo");
        }

        String token = jwtService.generateToken(user.getEmail());
        return new AuthResponse(token);
    }

}
