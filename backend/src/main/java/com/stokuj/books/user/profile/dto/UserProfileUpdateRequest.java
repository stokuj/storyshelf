package com.stokuj.books.user.profile.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record UserProfileUpdateRequest(
        @NotBlank(message = "Username cannot be blank")
        String username,

        @Size(max = 500, message = "Bio cannot exceed 500 characters")
        String bio,

        String avatarUrl) {
}
