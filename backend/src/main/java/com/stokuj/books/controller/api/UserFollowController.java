package com.stokuj.books.controller.api;

import com.stokuj.books.dto.follow.FollowResponse;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.domain.entity.UserFollow;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.UserFollowRepository;
import com.stokuj.books.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/users/{username}")
@PreAuthorize("hasRole('USER')")
public class UserFollowController {

    private final UserFollowRepository userFollowRepository;
    private final UserRepository userRepository;

    public UserFollowController(UserFollowRepository userFollowRepository,
                                UserRepository userRepository) {
        this.userFollowRepository = userFollowRepository;
        this.userRepository = userRepository;
    }

    @PostMapping("/follow")
    public ResponseEntity<Void> follow(@PathVariable String username,
                                       Authentication authentication) {
        if (userFollowRepository.existsByFollower_EmailAndFollowing_Username(
                authentication.getName(), username)) {
            throw new ConflictException("Już obserwujesz tego użytkownika");
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

    @DeleteMapping("/follow")
    public ResponseEntity<Void> unfollow(@PathVariable String username,
                                         Authentication authentication) {
        UserFollow follow = userFollowRepository
                .findByFollower_EmailAndFollowing_Username(authentication.getName(), username)
                .orElseThrow(() -> new ResourceNotFoundException("Nie obserwujesz tego użytkownika"));

        userFollowRepository.delete(follow);
        return ResponseEntity.noContent().build();
    }

    private FollowResponse toDto(UserFollow f) {
        return new FollowResponse(f.getId(), f.getFollower().getUsername(), f.getFollowing().getUsername(), f.getFollowedAt());
    }

    @GetMapping("/followers")
    public ResponseEntity<List<FollowResponse>> getFollowers(@PathVariable String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return ResponseEntity.ok(userFollowRepository.findAllByFollowing_Email(user.getEmail())
                .stream().map(this::toDto).toList());
    }

    @GetMapping("/following")
    public ResponseEntity<List<FollowResponse>> getFollowing(@PathVariable String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        return ResponseEntity.ok(userFollowRepository.findAllByFollower_Email(user.getEmail())
                .stream().map(this::toDto).toList());
    }
}
