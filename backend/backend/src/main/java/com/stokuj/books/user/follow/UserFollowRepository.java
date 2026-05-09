package com.stokuj.books.user.follow;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
public interface UserFollowRepository extends JpaRepository<UserFollow, Long> {
    boolean existsByFollower_EmailAndFollowing_Username(String followerEmail, String followingUsername);
    Optional<UserFollow> findByFollower_EmailAndFollowing_Username(String followerEmail, String followingUsername);
    List<UserFollow> findAllByFollower_Email(String email);
    List<UserFollow> findAllByFollowing_Email(String email);
}
