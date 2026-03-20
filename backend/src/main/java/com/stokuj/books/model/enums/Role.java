package com.stokuj.books.model.enums;

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
