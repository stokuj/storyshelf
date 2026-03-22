package com.stokuj.books.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public class AuthRequest {
    @Email(message = "Nieprawidlowy adres email")
    @NotBlank(message = "Email jest wymagany")
    private String email;

    @NotBlank(message = "Username jest wymagany")
    @jakarta.validation.constraints.Pattern(
            regexp = "[a-z]{3,30}",
            message = "Username musi mieć 3-30 małych liter (a-z)"
    )
    private String username;

    @NotBlank(message = "Haslo jest wymagane")
    private String password;

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }
}
