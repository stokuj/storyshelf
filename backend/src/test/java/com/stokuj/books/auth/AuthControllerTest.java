package com.stokuj.books.auth;

import com.stokuj.books.auth.dto.AuthMeResponse;
import com.stokuj.books.auth.dto.AuthResponse;
import com.stokuj.books.auth.dto.LoginRequest;
import com.stokuj.books.auth.dto.RegisterRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.profile.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
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
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.web.context.SecurityContextRepository;

import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    AuthService authService;
    @Mock
    AuthenticationManager authenticationManager;
    @Mock
    SecurityContextRepository securityContextRepository;
    @Mock
    UserService userService;
    @Mock
    HttpServletRequest httpRequest;
    @Mock
    HttpServletResponse httpResponse;
    @Mock
    Authentication authentication;

    @InjectMocks
    AuthController authController;

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
    class Register {

        @Test
        void shouldRegisterUserAndReturn201() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "secret123");
            User user = org.mockito.Mockito.mock(User.class);
            given(user.getUsername()).willReturn("john");
            given(authService.registerUser(request)).willReturn(user);

            ResponseEntity<AuthResponse> response = authController.register(request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().message()).isEqualTo("User registered successfully");
            assertThat(response.getBody().username()).isEqualTo("john");
        }

        @Test
        void shouldHaveValidationViolationsForInvalidRegisterPayload() {
            RegisterRequest request = new RegisterRequest("JO", "bad", "123");

            Set<ConstraintViolation<RegisterRequest>> violations = validator.validate(request);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("username"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("email"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("password"));
        }

        @Test
        void shouldPropagateConflictOnRegister() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "secret123");
            given(authService.registerUser(request)).willThrow(new ConflictException("Username is already taken."));

            assertThatThrownBy(() -> authController.register(request))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("Username is already taken.");
        }
    }

    @Nested
    class Login {

        @Test
        void shouldLoginAndReturn200() {
            LoginRequest request = new LoginRequest("john@example.com", "secret123");
            given(authenticationManager.authenticate(any())).willReturn(authentication);
            given(authentication.getName()).willReturn("john@example.com");

            ResponseEntity<AuthResponse> response = authController.login(request, httpRequest, httpResponse);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().message()).isEqualTo("Login successful");
            assertThat(response.getBody().username()).isEqualTo("john@example.com");
            verify(securityContextRepository).saveContext(any(), any(), any());
        }

        @Test
        void shouldPropagateUnauthorizedOnInvalidCredentials() {
            LoginRequest request = new LoginRequest("john@example.com", "wrong");
            given(authenticationManager.authenticate(any())).willThrow(new BadCredentialsException("Bad credentials"));

            assertThatThrownBy(() -> authController.login(request, httpRequest, httpResponse))
                    .isInstanceOf(BadCredentialsException.class);
        }

        @Test
        void shouldHaveValidationViolationsForInvalidLoginPayload() {
            LoginRequest request = new LoginRequest("bad", "");

            Set<ConstraintViolation<LoginRequest>> violations = validator.validate(request);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("email"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("password"));
        }
    }

    @Nested
    class Me {

        @Test
        void shouldReturnAnonymousStateWhenNoAuthentication() {
            ResponseEntity<AuthMeResponse> response = authController.me(null);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().authenticated()).isFalse();
            assertThat(response.getBody().email()).isNull();
            assertThat(response.getBody().username()).isNull();
            assertThat(response.getBody().role()).isNull();
        }

        @Test
        void shouldReturnAuthenticatedUserData() {
            given(authentication.isAuthenticated()).willReturn(true);
            given(authentication.getName()).willReturn("john@example.com");

            User user = org.mockito.Mockito.mock(User.class);
            given(user.getEmail()).willReturn("john@example.com");
            given(user.getUsername()).willReturn("john");
            given(userService.findByEmail("john@example.com")).willReturn(user);

            ResponseEntity<AuthMeResponse> response = authController.me(authentication);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().authenticated()).isTrue();
            assertThat(response.getBody().email()).isEqualTo("john@example.com");
            assertThat(response.getBody().username()).isEqualTo("john");
        }

        @Test
        void shouldReturnAnonymousStateWhenAuthenticationIsAnonymous() {
            Authentication anonymous = new AnonymousAuthenticationToken(
                    "key",
                    "anonymousUser",
                    List.of(new SimpleGrantedAuthority("ROLE_ANONYMOUS"))
            );

            ResponseEntity<AuthMeResponse> response = authController.me(anonymous);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().authenticated()).isFalse();
        }

        @Test
        void shouldPropagateNotFoundWhenUserDoesNotExist() {
            given(authentication.isAuthenticated()).willReturn(true);
            given(authentication.getName()).willReturn("john@example.com");
            given(userService.findByEmail("john@example.com"))
                    .willThrow(new ResourceNotFoundException("User not found"));

            assertThatThrownBy(() -> authController.me(authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }
    }
}
