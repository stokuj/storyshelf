package com.stokuj.books.dto.auth;

public record AuthResponse(
        String message,
        String username
) {}