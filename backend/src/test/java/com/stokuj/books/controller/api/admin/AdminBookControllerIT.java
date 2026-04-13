package com.stokuj.books.controller.api.admin;

public class AdminBookControllerIT {
    // TODO: Security: Verify 403 Forbidden block for regular user when editing a book (PUT/PATCH).
    // TODO: Input validation: Confirm that POST /api/admin/books rejects BookRequest without required title (400).
    // TODO: Input validation: Verify that the system rejects negative page count in PATCH request (according to @Min(0)).
    // TODO: Happy path: Simulate valid book creation by Moderator and verify returned JSON response format.
}
