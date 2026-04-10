package com.stokuj.books.dto.auth;

import com.stokuj.books.domain.enums.Role;

public record AuthMeResponse(
        boolean authenticated,
        String email,
        String username,
        Role role
) {
}
