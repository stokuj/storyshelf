package com.stokuj.books.auth;

import com.stokuj.books.auth.dto.LoginRequest;
import com.stokuj.books.auth.dto.RegisterRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.Set;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

class AuthDtoTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @BeforeAll
    static void setUpValidator() {
        validatorFactory = Validation.buildDefaultValidatorFactory();
        validator = validatorFactory.getValidator();
    }

    @AfterAll
    static void closeValidator() {
        validatorFactory.close();
    }

    private <T> Set<String> validate(T object) {
        return validator.validate(object).stream()
                .map(v -> v.getPropertyPath() + ":" + v.getMessage())
                .collect(Collectors.toSet());
    }

    // -------------------------------------------------------------------------
    // RegisterRequest
    // -------------------------------------------------------------------------

    @Nested
    class RegisterRequestTests {

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "secret123");
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- username ---

        @Test
        void shouldFailWhenUsernameIsBlank() {
            RegisterRequest request = new RegisterRequest("", "john@example.com", "secret123");
            assertThat(validate(request)).contains("username:Username cannot be blank");
        }

        @Test
        void shouldFailWhenUsernameContainsUppercase() {
            RegisterRequest request = new RegisterRequest("John", "john@example.com", "secret123");
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameContainsDigits() {
            RegisterRequest request = new RegisterRequest("john1", "john@example.com", "secret123");
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameIsTooShort() {
            RegisterRequest request = new RegisterRequest("ab", "john@example.com", "secret123");
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameIsTooLong() {
            RegisterRequest request = new RegisterRequest("a".repeat(31), "john@example.com", "secret123");
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldPassWhenUsernameIsAtMinLength() {
            RegisterRequest request = new RegisterRequest("abc", "john@example.com", "secret123");
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenUsernameIsAtMaxLength() {
            RegisterRequest request = new RegisterRequest("a".repeat(30), "john@example.com", "secret123");
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- email ---

        @Test
        void shouldFailWhenEmailIsBlank() {
            RegisterRequest request = new RegisterRequest("john", "", "secret123");
            assertThat(validate(request)).contains("email:Email cannot be blank");
        }

        @Test
        void shouldFailWhenEmailHasInvalidFormat() {
            RegisterRequest request = new RegisterRequest("john", "not-an-email", "secret123");
            assertThat(validate(request)).contains("email:Invalid email format");
        }

        @Test
        void shouldFailWhenEmailIsTooLong() {
            // 256 znaków, poprawny format
            String tooLongEmail = "a".repeat(249) + "@ex.com";
            RegisterRequest request = new RegisterRequest("john", tooLongEmail, "secret123");
            assertThat(validate(request)).contains("email:Email cannot exceed 255 characters");
        }

        // --- password ---

        @Test
        void shouldFailWhenPasswordIsBlank() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "");
            assertThat(validate(request)).contains("password:Password cannot be blank");
        }

        @Test
        void shouldFailWhenPasswordIsTooShort() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "abc");
            assertThat(validate(request))
                    .contains("password:Password must be between 6 and 72 characters long");
        }

        @Test
        void shouldFailWhenPasswordIsTooLong() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "x".repeat(73));
            assertThat(validate(request))
                    .contains("password:Password must be between 6 and 72 characters long");
        }

        @Test
        void shouldPassWhenPasswordIsAtMinLength() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "abcdef");
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenPasswordIsAtMaxLength() {
            RegisterRequest request = new RegisterRequest("john", "john@example.com", "x".repeat(72));
            assertThat(validator.validate(request)).isEmpty();
        }
    }

    // -------------------------------------------------------------------------
    // LoginRequest
    // -------------------------------------------------------------------------

    @Nested
    class LoginRequestTests {

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            LoginRequest request = new LoginRequest("john@example.com", "secret123");
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldFailWhenEmailIsBlank() {
            LoginRequest request = new LoginRequest("", "secret123");
            assertThat(validate(request)).contains("email:Email cannot be blank");
        }

        @Test
        void shouldFailWhenEmailHasInvalidFormat() {
            LoginRequest request = new LoginRequest("not-an-email", "secret123");
            assertThat(validate(request)).contains("email:Invalid email format");
        }

        @Test
        void shouldFailWhenPasswordIsBlank() {
            LoginRequest request = new LoginRequest("john@example.com", "");
            assertThat(validate(request)).contains("password:Password cannot be blank");
        }
    }
}