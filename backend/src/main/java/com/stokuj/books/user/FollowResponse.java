package com.stokuj.books.user;

import java.time.Instant;

public record FollowResponse(
        Long id,
        String followerUsername,
        String followingUsername,
        Instant followedAt
) {}
