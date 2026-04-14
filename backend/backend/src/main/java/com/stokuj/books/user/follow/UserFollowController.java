package com.stokuj.books.user.follow;

import com.stokuj.books.user.User;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.follow.dto.FollowResponse;
import com.stokuj.books.user.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;

import java.util.List;

@RestController
@RequestMapping("/api/users/{username}")
@PreAuthorize("hasRole('USER')")
@Tag(name = "User Follows", description = "Operations for following and unfollowing users")
public class UserFollowController {

    private final UserFollowRepository userFollowRepository;
    private final UserRepository userRepository;

    public UserFollowController(UserFollowRepository userFollowRepository,
                                UserRepository userRepository) {
        this.userFollowRepository = userFollowRepository;
        this.userRepository = userRepository;
    }

    @Operation(summary = "Follow a user", description = "Allows the authenticated user to follow another user by their username.")
    @ApiResponse(responseCode = "201", description = "Successfully followed the user")
    @ApiResponse(responseCode = "404", description = "User not found")
    @ApiResponse(responseCode = "409", description = "Already following this user")
    @PostMapping("/follow")
    public ResponseEntity<Void> follow(@PathVariable String username,
                                       Authentication authentication) {
        if (userFollowRepository.existsByFollower_EmailAndFollowing_Username(
                authentication.getName(), username)) {
            throw new ConflictException("You are already following this user");
        }

        User follower = userRepository.findByEmail(authentication.getName())
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        User following = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        UserFollow follow = new UserFollow();
        follow.setFollower(follower);
        follow.setFollowing(following);
        userFollowRepository.save(follow);

        return ResponseEntity.status(201).build();
    }

    @Operation(summary = "Unfollow a user", description = "Allows the authenticated user to unfollow another user by their username.")
    @ApiResponse(responseCode = "204", description = "Successfully unfollowed the user")
    @ApiResponse(responseCode = "404", description = "User not found or not currently following")
    @DeleteMapping("/follow")
    public ResponseEntity<Void> unfollow(@PathVariable String username,
                                         Authentication authentication) {
        UserFollow follow = userFollowRepository
                .findByFollower_EmailAndFollowing_Username(authentication.getName(), username)
                .orElseThrow(() -> new ResourceNotFoundException("You are not following this user"));

        userFollowRepository.delete(follow);
        return ResponseEntity.noContent().build();
    }

    private FollowResponse toDto(UserFollow f) {
        return new FollowResponse(f.getId(), f.getFollower().getUsername(), f.getFollowing().getUsername(), f.getFollowedAt());
    }

    @Operation(summary = "Get followers", description = "Retrieves a list of users following the specified user.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved followers list")
    @ApiResponse(responseCode = "404", description = "User not found")
    @GetMapping("/followers")
    public ResponseEntity<List<FollowResponse>> getFollowers(@PathVariable String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return ResponseEntity.ok(userFollowRepository.findAllByFollowing_Email(user.getEmail())
                .stream().map(this::toDto).toList());
    }

    @Operation(summary = "Get following", description = "Retrieves a list of users that the specified user is following.")
    @ApiResponse(responseCode = "200", description = "Successfully retrieved following list")
    @ApiResponse(responseCode = "404", description = "User not found")
    @GetMapping("/following")
    public ResponseEntity<List<FollowResponse>> getFollowing(@PathVariable String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return ResponseEntity.ok(userFollowRepository.findAllByFollower_Email(user.getEmail())
                .stream().map(this::toDto).toList());
    }
}
