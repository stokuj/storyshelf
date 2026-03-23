package com.stokuj.books.service;

import com.stokuj.books.domain.entity.User;
import com.stokuj.books.domain.enums.Role;
import com.stokuj.books.dto.auth.RegisterRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public User registerUser(RegisterRequest request) {
        if (userRepository.findByEmail(request.email()).isPresent()) {
            throw new ConflictException("Użytkownik z tym adresem email już istnieje.");
        }
        if (userRepository.existsByUsername(request.username())) {
            throw new ConflictException("Username jest już zajęty.");
        }

        User user = new User();
        user.setEmail(request.email());
        user.setPassword(passwordEncoder.encode(request.password()));
        user.setRole(Role.USER);
        user.setUsername(request.username());
        return userRepository.save(user);
    }
}