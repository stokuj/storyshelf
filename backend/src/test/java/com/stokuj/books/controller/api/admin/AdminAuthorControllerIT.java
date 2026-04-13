package com.stokuj.books.controller.api.admin;

public class AdminAuthorControllerIT {
    // TODO: Security: Verify that unauthenticated guest receives 401 when trying POST (add author).
    // TODO: Security: Verify that authenticated regular USER (without MODERATOR role) receives 403 Forbidden when trying to delete author (DELETE).
    // TODO: Security: Verify that MODERATOR has full access and receives 200/201 or 204.
    // TODO: Input validation: Ensure sending AuthorRequest with empty or null 'name' by Moderator results in 400 Bad Request.
    // TODO: Input validation: Verify that exceeding character limit (over 255) from @Size returns validation error.
}
