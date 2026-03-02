package com.stokuj.books.security;

import com.stokuj.books.model.User;
import com.stokuj.books.repository.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.jspecify.annotations.NonNull;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler implements AuthenticationSuccessHandler {

    private final UserRepository userRepository;
    private final JwtService jwtService;

    @Override
    public void onAuthenticationSuccess(@NonNull HttpServletRequest request,
                                        @NonNull HttpServletResponse response,
                                        Authentication authentication) throws IOException {

        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();

        // GitHub może zwrócić null jeśli email jest prywatny
        // wtedy używamy login@github.com jako zastępczy email
        String email = oAuth2User.getAttribute("email");
        if (email == null) {
            String login = oAuth2User.getAttribute("login");
            email = login + "@github.com";
        }

        final String finalEmail = email;

        userRepository.findByEmail(finalEmail).orElseGet(() -> {
            User newUser = new User();
            newUser.setEmail(finalEmail);
            newUser.setPassword("");
            newUser.setRole("ROLE_USER");
            return userRepository.save(newUser);
        });

        String token = jwtService.generateToken(finalEmail);
        response.setContentType("application/json");
        response.getWriter().write("{\"token\": \"" + token + "\"}");
    }
}