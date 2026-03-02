package com.stokuj.books.security;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtFilter jwtFilter;
    private final OAuth2SuccessHandler oAuth2SuccessHandler;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                // wyłączamy CSRF — nie potrzebujemy tego w REST API z JWT
                .csrf(csrf -> csrf.disable())

                // Spring nie trzyma sesji — każdy request musi mieć token
                .sessionManagement(session ->
                        session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                // które endpointy są publiczne a które wymagają tokenu
                .authorizeHttpRequests(auth -> auth
                        // rejestracja i logowanie — dostępne dla wszystkich
                        .requestMatchers("/api/auth/**").permitAll()
                        // Swagger — dostępny dla wszystkich
                        .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                        // GET książki — dostępne dla wszystkich
                        .requestMatchers(HttpMethod.GET, "/api/books/**").permitAll()
                        // reszta — tylko zalogowani
                        .anyRequest().authenticated()
                )

                // dodajemy obsługę OAuth2
                .oauth2Login(oauth2 -> oauth2
                        .successHandler(oAuth2SuccessHandler)
                )

                // dodaj nasz JwtFilter przed domyślnym filtrem Spring Security
                .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        // BCrypt — standardowy algorytm hashowania haseł
        // nigdy nie trzymamy hasła plaintext w bazie
        return new BCryptPasswordEncoder();
    }
}