package com.stokuj.books.user;

public enum UserRole {
    USER,
    MODERATOR,
    ADMIN;

    public boolean atLeast(UserRole other) {
        return this.ordinal() >= other.ordinal();
    }

    public String asAuthority() {
        return "ROLE_" + name();
    }
}
