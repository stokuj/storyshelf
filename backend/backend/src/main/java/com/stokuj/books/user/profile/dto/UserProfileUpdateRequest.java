package com.stokuj.books.user.profile.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record UserProfileUpdateRequest(
        @NotBlank(message = "Username cannot be blank")
        @Pattern(regexp = "^[a-z]{3,30}$", message = "Username must be 3-30 lowercase letters (a-z)")
        String username,

        @Size(max = 500, message = "Bio cannot exceed 500 characters")
        String bio,

        String avatarUrl
) {}