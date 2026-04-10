package com.stokuj.books.auth;

import com.stokuj.books.user.Role;

public record AuthMeResponse(
        boolean authenticated,
        String email,
        String username,
        Role role
) {
}
