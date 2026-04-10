package com.stokuj.books.user;

import java.time.LocalDateTime;

public record UserProfileResponse(String username,
                                  String bio,
                                  String avatarUrl,
                                  LocalDateTime memberSince) {
}
