package com.stokuj.books.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.jspecify.annotations.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
public class JwtFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final org.springframework.security.core.userdetails.UserDetailsService userDetailsService;

    public JwtFilter(JwtService jwtService, org.springframework.security.core.userdetails.UserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    @NonNull HttpServletResponse response,
                                    @NonNull FilterChain filterChain) throws ServletException, IOException {

        // pobierz header "Authorization" z requestu
        String authHeader = request.getHeader("Authorization");

        // jeśli nie ma headera lub nie zaczyna się od "Bearer " — przepuść bez autoryzacji
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        // wytnij "Bearer " i zostaw sam token
        String token = authHeader.substring(7);

        // sprawdź czy token jest ważny
        if (jwtService.isTokenValid(token)) {
            String email = jwtService.extractEmail(token);
            org.springframework.security.core.userdetails.UserDetails userDetails = userDetailsService.loadUserByUsername(email);

            // powiedz Springowi że użytkownik jest zalogowany
            UsernamePasswordAuthenticationToken auth =
                    new UsernamePasswordAuthenticationToken(
                            userDetails,
                            null,
                            userDetails.getAuthorities()
                    );

            SecurityContextHolder.getContext().setAuthentication(auth);
        }

        filterChain.doFilter(request, response);
    }
}
