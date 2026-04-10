package com.stokuj.books.user;

import com.stokuj.books.user.UserRole;
import java.time.LocalDateTime;

public record UserSettingsResponse(String username,
                                   String bio,
                                   String avatarUrl,
                                   LocalDateTime memberSince,
                                   boolean profilePublic,
                                   String email,
                                   UserRole role) {
}
