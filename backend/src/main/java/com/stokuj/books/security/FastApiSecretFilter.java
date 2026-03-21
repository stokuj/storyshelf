package com.stokuj.books.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class FastApiSecretFilter extends OncePerRequestFilter {

    @Value("${fastapi.internal.secret:default-secret-change-me}")
    private String secret;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        if (request.getRequestURI().startsWith("/api/fastAPI/")) {
            // Apply only to POST endpoints as requested, or explicitly all under /fastAPI/
            if (request.getMethod().equalsIgnoreCase("POST")) {
                String header = request.getHeader("X-FastAPI-Secret");
                if (header == null || !header.equals(secret)) {
                    response.setStatus(403);
                    response.getWriter().write("Forbidden: Invalid FastAPI Secret");
                    return;
                }
            }
        }
        
        filterChain.doFilter(request, response);
    }
}
