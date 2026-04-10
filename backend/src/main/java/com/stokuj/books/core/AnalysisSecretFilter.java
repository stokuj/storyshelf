package com.stokuj.books.core;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class AnalysisSecretFilter extends OncePerRequestFilter {

    @Value("${analysis.internal.secret:default-secret-change-me}")
    private String secret;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        if (request.getRequestURI().startsWith("/api/integration/analysis/")) {
            if (request.getMethod().equalsIgnoreCase("POST")) {
                String header = request.getHeader("X-Analysis-Secret");
                if (header == null || !header.equals(secret)) {
                    response.setStatus(403);
                    response.getWriter().write("Forbidden: Invalid Analysis Secret");
                    return;
                }
            }
        }
        
        filterChain.doFilter(request, response);
    }
}
