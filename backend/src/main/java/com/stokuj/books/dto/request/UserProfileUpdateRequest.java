package com.stokuj.books.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import org.hibernate.validator.constraints.URL;

public record UserProfileUpdateRequest(
        @NotBlank(message = "Username jest wymagany")
        @Pattern(regexp = "[a-z]{3,30}", message = "Username musi mieć 3-30 małych liter (a-z)")
        String username,
        @Size(max = 500, message = "Bio może mieć maksymalnie 500 znaków")
        String bio,
        @URL(message = "Avatar URL musi być poprawnym adresem")
        String avatarUrl
) {
}
