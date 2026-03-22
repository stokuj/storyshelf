package com.stokuj.books.dto.user;

public record UserProfileUpdateRequest(String username,
                                       String bio,
                                       String avatarUrl) {
}
