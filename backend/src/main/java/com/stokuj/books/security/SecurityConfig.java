package com.stokuj.books.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    private final FastApiSecretFilter fastApiSecretFilter;

    public SecurityConfig(FastApiSecretFilter fastApiSecretFilter) {
        this.fastApiSecretFilter = fastApiSecretFilter;
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .csrf(csrf -> csrf.ignoringRequestMatchers("/api/**"))
                .cors(Customizer.withDefaults())
                .headers(headers -> headers
                        .httpStrictTransportSecurity(hsts -> hsts.disable())
                )
                .sessionManagement(session -> session
                        .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
                )
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(HttpMethod.OPTIONS, "/**").permitAll()
                        .requestMatchers("/api/auth/**").permitAll()
                        .requestMatchers("/docs/**", "/swagger-ui/**", "/v3/api-docs/**").permitAll()
                        .requestMatchers("/login", "/register", "/error").permitAll()
                        .requestMatchers(HttpMethod.GET, "/", "/home", "/book/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/books/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/search").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/users/*/profile").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/authors/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/series/**").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/books/*/chapters").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/books/*/characters").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/books/*/relations").permitAll()
                        .requestMatchers(HttpMethod.GET, "/api/users/**").permitAll()
                        .requestMatchers("/api/shelf/**").hasRole("USER")
                        .requestMatchers("/api/users/me/**").hasRole("USER")
                        .requestMatchers("/api/users/*/follow").hasRole("USER")
                        .requestMatchers("/api/admin/**").hasRole("MODERATOR")
                        .requestMatchers(HttpMethod.PATCH, "/api/fastapi/chapters/*/analyse-result").permitAll()
                        .requestMatchers(HttpMethod.PATCH, "/api/fastapi/chapters/*/ner-result").permitAll()
                        .requestMatchers(HttpMethod.PATCH, "/api/fastapi/books/*/find-pairs-result").permitAll()
                        .requestMatchers(HttpMethod.PATCH, "/api/fastapi/books/*/relations-result").permitAll()
                        .requestMatchers(HttpMethod.POST, "/book/*/review").hasRole("USER")
                        .requestMatchers("/profile/**").permitAll()
                        .requestMatchers("/admin/reviews/**").hasRole("MODERATOR")
                        .requestMatchers("/admin/users/**").hasRole("MODERATOR")
                        .requestMatchers("/admin/system").hasRole("ADMIN")
                        .requestMatchers("/admin/**").hasRole("MODERATOR")
                        .requestMatchers("/books/propose", "/settings", "/settings/**").hasRole("USER")
                        .anyRequest().authenticated()
                )
                .formLogin(form -> form
                        .loginPage("/login")
                        .defaultSuccessUrl("/", true)
                        .failureUrl("/login?error")
                        .permitAll()
                )
                .logout(logout -> logout
                        .logoutUrl("/logout")
                        .logoutSuccessUrl("/login?logout")
                        .invalidateHttpSession(true)
                        .deleteCookies("JSESSIONID")
                        .permitAll()
                )
                .exceptionHandling(exceptions -> exceptions
                        .authenticationEntryPoint((request, response, authException) -> {
                            if (request.getRequestURI().startsWith("/api/")) {
                                response.setStatus(401);
                                response.setContentType("application/json");
                                response.getWriter().write(
                                        "{\"status\":401,\"error\":\"Unauthorized\",\"message\":\"Brak lub niepoprawny token\",\"path\":\""
                                                + request.getRequestURI() + "\"}");
                                return;
                            }
                            response.sendRedirect("/login");
                        })
                        .accessDeniedPage("/error?status=403")
                )
                .addFilterBefore(fastApiSecretFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public org.springframework.security.authentication.AuthenticationManager authenticationManager(org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public org.springframework.security.web.context.SecurityContextRepository securityContextRepository() {
        return new org.springframework.security.web.context.HttpSessionSecurityContextRepository();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOriginPatterns(List.of("*"));
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("*"));
        configuration.setAllowCredentials(false);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
