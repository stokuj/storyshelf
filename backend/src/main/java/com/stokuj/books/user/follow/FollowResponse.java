package com.stokuj.books.user.follow;

import java.time.Instant;

public record FollowResponse(
        Long id,
        String followerUsername,
        String followingUsername,
        Instant followedAt
) {}
