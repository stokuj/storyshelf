package com.stokuj.books.dto.response;

import com.stokuj.books.model.enums.Role;
import java.time.LocalDateTime;

public record UserSettingsResponse(
        String username,
        String bio,
        String avatarUrl,
        LocalDateTime memberSince,
        boolean profilePublic,
        String email,
        Role role
) {
}
