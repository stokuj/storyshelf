package com.stokuj.books.auth;

import com.stokuj.books.user.UserRole;

public record AuthMeResponse(
        boolean authenticated,
        String email,
        String username,
        UserRole role
) {
}
