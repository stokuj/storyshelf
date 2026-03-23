package com.stokuj.books.dto.user;

import com.stokuj.books.domain.enums.Role;
import java.time.LocalDateTime;

public record UserSettingsResponse(String username,
                                   String bio,
                                   String avatarUrl,
                                   LocalDateTime memberSince,
                                   boolean profilePublic,
                                   String email,
                                   Role role) {
}
