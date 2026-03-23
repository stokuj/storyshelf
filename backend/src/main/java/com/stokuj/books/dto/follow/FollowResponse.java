package com.stokuj.books.dto.follow;

import java.time.Instant;

public record FollowResponse(
        Long id,
        String followerUsername,
        String followingUsername,
        Instant followedAt
) {}