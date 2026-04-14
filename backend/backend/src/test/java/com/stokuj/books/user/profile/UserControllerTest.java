package com.stokuj.books.user.profile;

import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRole;
import com.stokuj.books.user.profile.dto.UserProfileResponse;
import com.stokuj.books.user.profile.dto.UserProfileUpdateRequest;
import com.stokuj.books.user.profile.dto.UserSettingsResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.lang.reflect.Field;
import java.util.Collection;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class UserControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    UserService userService;

    @Mock
    Authentication authentication;

    @InjectMocks
    UserController userController;

    @BeforeAll
    static void setUpValidator() {
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    @Nested
    class GetProfile {

        @Test
        void shouldReturnPublicProfileForAnonymousUser() {
            User user = user("john", "john@example.com", true);
            UserProfileResponse response = new UserProfileResponse("john", "bio", null, LocalDateTime.now());
            given(userService.findByUsername("john")).willReturn(user);
            given(userService.toPublicResponse(user)).willReturn(response);

            ResponseEntity<UserProfileResponse> result = userController.getProfile("john", null);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(response);
        }

        @Test
        void shouldThrowWhenProfileIsPrivateForAnonymousUser() {
            User user = user("john", "john@example.com", false);
            given(userService.findByUsername("john")).willReturn(user);

            assertThatThrownBy(() -> userController.getProfile("john", null))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User does not exist");
        }

        @Test
        void shouldReturnPrivateProfileForOwner() {
            User user = user("john", "john@example.com", false);
            UserProfileResponse response = new UserProfileResponse("john", "bio", null, LocalDateTime.now());
            given(userService.findByUsername("john")).willReturn(user);
            given(userService.toPublicResponse(user)).willReturn(response);
            given(authentication.isAuthenticated()).willReturn(true);
            given(authentication.getName()).willReturn("john@example.com");
            given(authentication.getAuthorities()).willReturn(List.of());

            ResponseEntity<UserProfileResponse> result = userController.getProfile("john", authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(response);
        }

        @Test
        void shouldReturnPrivateProfileForPrivilegedRole() {
            User user = user("john", "john@example.com", false);
            UserProfileResponse response = new UserProfileResponse("john", "bio", null, LocalDateTime.now());
            given(userService.findByUsername("john")).willReturn(user);
            given(userService.toPublicResponse(user)).willReturn(response);
            given(authentication.isAuthenticated()).willReturn(true);
            given(authentication.getName()).willReturn("admin@example.com");
            List<GrantedAuthority> authorities = List.of(new SimpleGrantedAuthority("ROLE_MODERATOR"));
            org.mockito.Mockito.doReturn((Collection<? extends GrantedAuthority>) authorities)
                    .when(authentication)
                    .getAuthorities();

            ResponseEntity<UserProfileResponse> result = userController.getProfile("john", authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(response);
        }

        @Test
        void shouldPropagateWhenUserNotFound() {
            given(userService.findByUsername("missing"))
                    .willThrow(new ResourceNotFoundException("User does not exist"));

            assertThatThrownBy(() -> userController.getProfile("missing", null))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User does not exist");
        }
    }

    @Nested
    class Me {

        @Test
        void shouldReturnCurrentUserSettings() {
            User user = user("john", "john@example.com", true);
            UserSettingsResponse settings = new UserSettingsResponse(
                    "john",
                    "bio",
                    null,
                    LocalDateTime.now(),
                    true,
                    "john@example.com",
                    UserRole.USER
            );
            given(authentication.getName()).willReturn("john@example.com");
            given(userService.findByEmail("john@example.com")).willReturn(user);
            given(userService.toSettingsResponse(user)).willReturn(settings);

            ResponseEntity<UserSettingsResponse> result = userController.getMe(authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(settings);
        }
    }

    @Nested
    class UpdateProfile {

        @Test
        void shouldUpdateProfile() {
            User user = user("john", "john@example.com", true);
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("johnny", "new bio", "https://avatar");
            UserSettingsResponse settings = new UserSettingsResponse(
                    "johnny",
                    "new bio",
                    "https://avatar",
                    LocalDateTime.now(),
                    true,
                    "john@example.com",
                    UserRole.USER
            );

            given(authentication.getName()).willReturn("john@example.com");
            given(userService.findByEmail("john@example.com")).willReturn(user);
            given(userService.updateProfile(user, request)).willReturn(settings);

            ResponseEntity<UserSettingsResponse> result = userController.updateProfile(request, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(settings);
        }

        @Test
        void shouldPropagateConflictWhenUsernameIsTaken() {
            User user = user("john", "john@example.com", true);
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("taken", "new bio", null);
            given(authentication.getName()).willReturn("john@example.com");
            given(userService.findByEmail("john@example.com")).willReturn(user);
            given(userService.updateProfile(user, request))
                    .willThrow(new ConflictException("Username is already taken"));

            assertThatThrownBy(() -> userController.updateProfile(request, authentication))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("Username is already taken");
        }

        @Test
        void shouldHaveValidationViolationsForInvalidUpdateRequest() {
            UserProfileUpdateRequest invalid = new UserProfileUpdateRequest("A", "b".repeat(501), null);

            Set<ConstraintViolation<UserProfileUpdateRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("username"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("bio"));
        }
    }

    @Nested
    class UpdateVisibility {

        @Test
        void shouldUpdateVisibility() {
            User user = user("john", "john@example.com", true);
            UserSettingsResponse settings = new UserSettingsResponse(
                    "john",
                    "bio",
                    null,
                    LocalDateTime.now(),
                    false,
                    "john@example.com",
                    UserRole.USER
            );
            given(authentication.getName()).willReturn("john@example.com");
            given(userService.findByEmail("john@example.com")).willReturn(user);
            given(userService.updateVisibility(user, false)).willReturn(settings);

            ResponseEntity<UserSettingsResponse> result = userController.updateVisibility(false, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(settings);
        }
    }

    private User user(String username, String email, boolean profilePublic) {
        User user = new User();
        setField(user, "username", username);
        setField(user, "email", email);
        setField(user, "profilePublic", profilePublic);
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
}
