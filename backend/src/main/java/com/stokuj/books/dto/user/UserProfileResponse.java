package com.stokuj.books.dto.user;

import java.time.LocalDateTime;

public record UserProfileResponse(String username,
                                  String bio,
                                  String avatarUrl,
                                  LocalDateTime memberSince) {
}
