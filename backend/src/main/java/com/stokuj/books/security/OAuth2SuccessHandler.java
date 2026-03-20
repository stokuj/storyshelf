package com.stokuj.books.security;

import com.stokuj.books.model.entity.User;
import com.stokuj.books.model.enums.Role;
import com.stokuj.books.repository.UserRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.jspecify.annotations.NonNull;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.authority.mapping.GrantedAuthoritiesMapper;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.AuthenticationSuccessHandler;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.Collection;
import java.util.List;

@Component
public class OAuth2SuccessHandler implements AuthenticationSuccessHandler {

    private final UserRepository userRepository;
    private final GrantedAuthoritiesMapper authoritiesMapper;

    public OAuth2SuccessHandler(UserRepository userRepository,
                                GrantedAuthoritiesMapper authoritiesMapper) {
        this.userRepository = userRepository;
        this.authoritiesMapper = authoritiesMapper;
    }

    @Override
    public void onAuthenticationSuccess(@NonNull HttpServletRequest request,
                                        @NonNull HttpServletResponse response,
                                        Authentication authentication) throws IOException {

        OAuth2User oAuth2User = (OAuth2User) authentication.getPrincipal();

        String email = oAuth2User.getAttribute("email");
        if (email == null || email.isBlank()) {
            String login = oAuth2User.getAttribute("login");
            email = login + "@users.noreply.github.com";
        }

        final String finalEmail = email;
        User user = userRepository.findByEmail(finalEmail).orElseGet(() -> {
            User newUser = new User();
            newUser.setEmail(finalEmail);
            newUser.setPassword("OAUTH2_ACCOUNT");
            newUser.setRole(Role.USER);
            newUser.setUsername(generateUsername(finalEmail));
            newUser.setProvider("github");
            Object providerId = oAuth2User.getAttribute("id");
            if (providerId != null) {
                newUser.setProviderId(String.valueOf(providerId));
            }
            return userRepository.save(newUser);
        });

        Collection<? extends GrantedAuthority> authorities = authoritiesMapper.mapAuthorities(
                List.of(new SimpleGrantedAuthority(user.getRole().asAuthority()))
        );

        // Ustaw sesję Spring Security (zaloguj użytkownika przez sesję webową)
        org.springframework.security.authentication.UsernamePasswordAuthenticationToken sessionAuth =
                new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(
                        user.getEmail(),
                        null,
                        authorities
                );
        SecurityContextHolder.getContext().setAuthentication(sessionAuth);
        new HttpSessionSecurityContextRepository().saveContext(SecurityContextHolder.getContext(), request, response);

        response.sendRedirect("/");
    }

    private String generateUsername(String email) {
        String base = email.split("@", 2)[0].toLowerCase();
        String candidate = base;
        int counter = 1;
        while (userRepository.existsByUsername(candidate)) {
            candidate = base + counter;
            counter++;
        }
        return candidate;
    }
}
