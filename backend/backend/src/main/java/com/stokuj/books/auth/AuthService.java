package com.stokuj.books.auth;

import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRole;
import com.stokuj.books.auth.dto.RegisterRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.user.UserRepository;
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
            throw new ConflictException("Email is already taken.");
        }
        if (userRepository.existsByUsername(request.username())) {
            throw new ConflictException("Username is already taken.");
        }

        User user = new User();
        user.setEmail(request.email());
        user.setPassword(passwordEncoder.encode(request.password()));
        user.setRole(UserRole.USER);
        user.setUsername(request.username());
        return userRepository.save(user);
    }
}
