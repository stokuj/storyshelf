package com.stokuj.books.user.follow.dto;

import java.time.Instant;

public record FollowResponse(
        Long id,
        String followerUsername,
        String followingUsername,
        Instant followedAt
) {}
