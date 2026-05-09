package com.stokuj.books.auth.dto;

import com.stokuj.books.user.UserRole;

public record AuthMeResponse(
        boolean authenticated,
        String email,
        String username,
        UserRole role
) {
}
