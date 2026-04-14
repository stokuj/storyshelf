package com.stokuj.books.user.follow;

import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import com.stokuj.books.user.follow.dto.FollowResponse;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;

import java.lang.reflect.Field;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class UserFollowControllerTest {

    @Mock
    UserFollowRepository userFollowRepository;

    @Mock
    UserRepository userRepository;

    @Mock
    Authentication authentication;

    @InjectMocks
    UserFollowController userFollowController;

    @Nested
    class Follow {

        @Test
        void shouldFollowUserAndReturnCreated() {
            given(authentication.getName()).willReturn("john@example.com");
            given(userFollowRepository.existsByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(false);

            User follower = user("john", "john@example.com");
            User following = user("anna", "anna@example.com");
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(follower));
            given(userRepository.findByUsername("anna")).willReturn(Optional.of(following));

            ResponseEntity<Void> response = userFollowController.follow("anna", authentication);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            verify(userFollowRepository).save(org.mockito.ArgumentMatchers.any(UserFollow.class));
        }

        @Test
        void shouldThrowConflictWhenAlreadyFollowing() {
            given(authentication.getName()).willReturn("john@example.com");
            given(userFollowRepository.existsByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(true);

            assertThatThrownBy(() -> userFollowController.follow("anna", authentication))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("You are already following this user");
        }

        @Test
        void shouldThrowWhenFollowerNotFound() {
            given(authentication.getName()).willReturn("john@example.com");
            given(userFollowRepository.existsByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(false);
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userFollowController.follow("anna", authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }

        @Test
        void shouldThrowWhenFollowingNotFound() {
            given(authentication.getName()).willReturn("john@example.com");
            given(userFollowRepository.existsByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(false);
            User follower = user("john", "john@example.com");
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(follower));
            given(userRepository.findByUsername("anna")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userFollowController.follow("anna", authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }
    }

    @Nested
    class Unfollow {

        @Test
        void shouldUnfollowAndReturnNoContent() {
            given(authentication.getName()).willReturn("john@example.com");
            UserFollow follow = follow(1L, user("john", "john@example.com"), user("anna", "anna@example.com"));
            given(userFollowRepository.findByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(Optional.of(follow));

            ResponseEntity<Void> response = userFollowController.unfollow("anna", authentication);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
            verify(userFollowRepository).delete(follow);
        }

        @Test
        void shouldThrowWhenUnfollowMissingRelationship() {
            given(authentication.getName()).willReturn("john@example.com");
            given(userFollowRepository.findByFollower_EmailAndFollowing_Username("john@example.com", "anna"))
                    .willReturn(Optional.empty());

            assertThatThrownBy(() -> userFollowController.unfollow("anna", authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("You are not following this user");
        }
    }

    @Nested
    class Followers {

        @Test
        void shouldReturnFollowersList() {
            User user = user("anna", "anna@example.com");
            given(userRepository.findByUsername("anna")).willReturn(Optional.of(user));

            UserFollow f1 = follow(1L, user("john", "john@example.com"), user);
            UserFollow f2 = follow(2L, user("kate", "kate@example.com"), user);
            given(userFollowRepository.findAllByFollowing_Email("anna@example.com")).willReturn(List.of(f1, f2));

            ResponseEntity<List<FollowResponse>> response = userFollowController.getFollowers("anna");

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).followerUsername()).isEqualTo("john");
            assertThat(response.getBody().get(1).followerUsername()).isEqualTo("kate");
        }

        @Test
        void shouldThrowWhenFollowersUserNotFound() {
            given(userRepository.findByUsername("missing")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userFollowController.getFollowers("missing"))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }
    }

    @Nested
    class Following {

        @Test
        void shouldReturnFollowingList() {
            User user = user("john", "john@example.com");
            given(userRepository.findByUsername("john")).willReturn(Optional.of(user));

            UserFollow f1 = follow(1L, user, user("anna", "anna@example.com"));
            UserFollow f2 = follow(2L, user, user("mark", "mark@example.com"));
            given(userFollowRepository.findAllByFollower_Email("john@example.com")).willReturn(List.of(f1, f2));

            ResponseEntity<List<FollowResponse>> response = userFollowController.getFollowing("john");

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).followingUsername()).isEqualTo("anna");
            assertThat(response.getBody().get(1).followingUsername()).isEqualTo("mark");
        }

        @Test
        void shouldThrowWhenFollowingUserNotFound() {
            given(userRepository.findByUsername("missing")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userFollowController.getFollowing("missing"))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }
    }

    private User user(String username, String email) {
        User user = new User();
        setField(user, "username", username);
        setField(user, "email", email);
        return user;
    }

    private UserFollow follow(Long id, User follower, User following) {
        UserFollow follow = new UserFollow();
        setField(follow, "id", id);
        setField(follow, "follower", follower);
        setField(follow, "following", following);
        setField(follow, "followedAt", Instant.now());
        return follow;
    }

    private void setField(Object target, String fieldName, Object value) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
