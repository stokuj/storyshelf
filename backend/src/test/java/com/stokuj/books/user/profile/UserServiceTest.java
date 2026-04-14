package com.stokuj.books.user.profile;

import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import com.stokuj.books.user.UserRole;
import com.stokuj.books.user.profile.dto.UserProfileResponse;
import com.stokuj.books.user.profile.dto.UserProfileUpdateRequest;
import com.stokuj.books.user.profile.dto.UserSettingsResponse;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    UserRepository userRepository;

    @InjectMocks
    UserService userService;

    @Nested
    class Finders {

        @Test
        void shouldFindByUsername() {
            User user = user("john", "john@example.com");
            given(userRepository.findByUsername("john")).willReturn(Optional.of(user));

            User result = userService.findByUsername("john");

            assertThat(result).isEqualTo(user);
        }

        @Test
        void shouldThrowWhenUsernameDoesNotExist() {
            given(userRepository.findByUsername("missing")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userService.findByUsername("missing"))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User does not exist");
        }

        @Test
        void shouldFindByEmail() {
            User user = user("john", "john@example.com");
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));

            User result = userService.findByEmail("john@example.com");

            assertThat(result).isEqualTo(user);
        }

        @Test
        void shouldThrowWhenEmailDoesNotExist() {
            given(userRepository.findByEmail("missing@example.com")).willReturn(Optional.empty());

            assertThatThrownBy(() -> userService.findByEmail("missing@example.com"))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User does not exist");
        }

        @Test
        void shouldFindById() {
            User user = user("john", "john@example.com");
            given(userRepository.findById(1L)).willReturn(Optional.of(user));

            User result = userService.findById(1L);

            assertThat(result).isEqualTo(user);
        }

        @Test
        void shouldThrowWhenIdDoesNotExist() {
            given(userRepository.findById(99L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> userService.findById(99L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User does not exist");
        }
    }

    @Nested
    class Mapping {

        @Test
        void shouldMapToPublicResponse() {
            Instant createdAt = Instant.parse("2025-01-10T12:34:56Z");
            User user = user("john", "john@example.com");
            setField(user, "bio", "Reader and writer");
            setField(user, "avatarUrl", "https://cdn/avatar.png");
            setField(user, "createdAt", createdAt);

            UserProfileResponse response = userService.toPublicResponse(user);

            assertThat(response.username()).isEqualTo("john");
            assertThat(response.bio()).isEqualTo("Reader and writer");
            assertThat(response.avatarUrl()).isEqualTo("https://cdn/avatar.png");
            assertThat(response.memberSince()).isEqualTo(LocalDateTime.ofInstant(createdAt, ZoneOffset.UTC));
        }

        @Test
        void shouldMapToPublicResponseWithNullMemberSinceWhenCreatedAtMissing() {
            User user = user("john", "john@example.com");

            UserProfileResponse response = userService.toPublicResponse(user);

            assertThat(response.memberSince()).isNull();
        }

        @Test
        void shouldMapToSettingsResponse() {
            Instant createdAt = Instant.parse("2024-05-01T08:00:00Z");
            User user = user("john", "john@example.com");
            setField(user, "bio", "Bio text");
            setField(user, "avatarUrl", "https://cdn/avatar.png");
            setField(user, "profilePublic", false);
            setField(user, "role", UserRole.MODERATOR);
            setField(user, "createdAt", createdAt);

            UserSettingsResponse response = userService.toSettingsResponse(user);

            assertThat(response.username()).isEqualTo("john");
            assertThat(response.bio()).isEqualTo("Bio text");
            assertThat(response.avatarUrl()).isEqualTo("https://cdn/avatar.png");
            assertThat(response.profilePublic()).isFalse();
            assertThat(response.email()).isEqualTo("john@example.com");
            assertThat(response.role()).isEqualTo(UserRole.MODERATOR);
            assertThat(response.memberSince()).isEqualTo(LocalDateTime.ofInstant(createdAt, ZoneOffset.UTC));
        }
    }

    @Nested
    class UpdateProfile {

        @Test
        void shouldUpdateProfile() {
            User user = user("john", "john@example.com");
            setField(user, "bio", "old bio");
            setField(user, "avatarUrl", "old-avatar");
            setField(user, "profilePublic", true);
            setField(user, "role", UserRole.USER);

            UserProfileUpdateRequest request = new UserProfileUpdateRequest("johnny", "new bio", "new-avatar");
            given(userRepository.existsByUsername("johnny")).willReturn(false);
            given(userRepository.save(user)).willReturn(user);

            UserSettingsResponse response = userService.updateProfile(user, request);

            assertThat(getField(user, "username")).isEqualTo("johnny");
            assertThat(getField(user, "bio")).isEqualTo("new bio");
            assertThat(getField(user, "avatarUrl")).isEqualTo("new-avatar");
            assertThat(response.username()).isEqualTo("johnny");
        }

        @Test
        void shouldAllowSameUsernameWithoutConflictCheck() {
            User user = user("john", "john@example.com");
            setField(user, "profilePublic", true);
            setField(user, "role", UserRole.USER);
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", "updated bio", null);
            given(userRepository.save(user)).willReturn(user);

            UserSettingsResponse response = userService.updateProfile(user, request);

            verify(userRepository, never()).existsByUsername("john");
            assertThat(response.username()).isEqualTo("john");
            assertThat(getField(user, "bio")).isEqualTo("updated bio");
        }

        @Test
        void shouldNotOverrideBioOrAvatarWhenNullInRequest() {
            User user = user("john", "john@example.com");
            setField(user, "bio", "existing bio");
            setField(user, "avatarUrl", "existing-avatar");
            setField(user, "profilePublic", true);
            setField(user, "role", UserRole.USER);

            UserProfileUpdateRequest request = new UserProfileUpdateRequest("johnny", null, null);
            given(userRepository.existsByUsername("johnny")).willReturn(false);
            given(userRepository.save(user)).willReturn(user);

            userService.updateProfile(user, request);

            assertThat(getField(user, "bio")).isEqualTo("existing bio");
            assertThat(getField(user, "avatarUrl")).isEqualTo("existing-avatar");
        }

        @Test
        void shouldThrowConflictWhenUsernameAlreadyTaken() {
            User user = user("john", "john@example.com");
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("taken", "bio", null);
            given(userRepository.existsByUsername("taken")).willReturn(true);

            assertThatThrownBy(() -> userService.updateProfile(user, request))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("Username is already taken");
        }
    }

    @Nested
    class UpdateVisibility {

        @Test
        void shouldUpdateVisibility() {
            User user = user("john", "john@example.com");
            setField(user, "profilePublic", true);
            setField(user, "role", UserRole.USER);
            given(userRepository.save(user)).willReturn(user);

            UserSettingsResponse response = userService.updateVisibility(user, false);

            assertThat(getField(user, "profilePublic")).isEqualTo(false);
            assertThat(response.profilePublic()).isFalse();
        }
    }

    private User user(String username, String email) {
        User user = new User();
        setField(user, "username", username);
        setField(user, "email", email);
        return user;
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

    private Object getField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
