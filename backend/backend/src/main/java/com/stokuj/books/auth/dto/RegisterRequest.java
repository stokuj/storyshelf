package com.stokuj.books.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank(message = "Username cannot be blank")
        @Pattern(regexp = "^[a-z]{3,30}$", message = "Username must be 3-30 lowercase letters (a-z)")
        String username,

        @Email(message = "Invalid email format")
        @NotBlank(message = "Email cannot be blank")
        @Size(max = 255, message = "Email cannot exceed 255 characters")
        String email,

        @NotBlank(message = "Password cannot be blank")
        @Size(min = 6, max = 72, message = "Password must be between 6 and 72 characters long")
        String password
) {}
