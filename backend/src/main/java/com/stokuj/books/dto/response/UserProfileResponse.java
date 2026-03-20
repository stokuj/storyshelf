package com.stokuj.books.dto.response;

import java.time.LocalDateTime;

public record UserProfileResponse(
        String username,
        String bio,
        String avatarUrl,
        LocalDateTime memberSince
) {
}
