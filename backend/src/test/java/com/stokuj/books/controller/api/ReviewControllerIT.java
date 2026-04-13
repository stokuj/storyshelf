package com.stokuj.books.controller.api;

public class ReviewControllerIT {
    // TODO: Authorization: Fetching reviews (GET) should be available to unauthenticated guests (200 OK).
    // TODO: Security: Attempt to add rating (POST) by anonymous user should be rejected (401).
    // TODO: Validation (critical): Sending ReviewRequest with rating '9' (or -1) by authenticated user should be blocked by @Max(5).
    // TODO: Validation: Review content limit - sending too large a string should return size validation error.
}
