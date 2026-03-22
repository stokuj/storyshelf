package com.stokuj.books.domain.enums;

public enum Role {
    USER,
    MODERATOR,
    ADMIN;

    public boolean atLeast(Role other) {
        return this.ordinal() >= other.ordinal();
    }

    public String asAuthority() {
        return "ROLE_" + name();
    }
}
