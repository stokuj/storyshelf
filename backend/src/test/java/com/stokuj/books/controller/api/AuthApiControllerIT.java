package com.stokuj.books.controller.api;

public class AuthApiControllerIT {
    // TODO: Registration - Validation: Verify that too short password (less than 6 chars) in RegisterRequest returns clear validation error (400).
    // TODO: Registration - Validation: Send invalid email format (without @) and ensure @Email rejects it correctly.
    // TODO: Registration - Conflict: Verify that registration with already used email returns clean 409 Conflict JSON.
    // TODO: Login: Test successful login for valid user and session token/cookie issuance (200 OK).
    // TODO: Login: Simulate invalid login/password and expect 401 Unauthorized.
}
