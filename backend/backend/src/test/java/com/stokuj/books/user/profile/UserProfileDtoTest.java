package com.stokuj.books.user.profile;

import com.stokuj.books.user.profile.dto.UserProfileUpdateRequest;
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

class UserProfileUpdateRequestDtoTest {

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

    @Nested
    class UserProfileUpdateRequestTests {

        // --- happy path ---

        @Test
        void shouldPassWhenOnlyUsernameIsProvided() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", "My bio.", "https://example.com/avatar.jpg");
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- username ---

        @Test
        void shouldFailWhenUsernameIsBlank() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("", null, null);
            assertThat(validate(request)).contains("username:Username cannot be blank");
        }

        @Test
        void shouldFailWhenUsernameContainsUppercase() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("John", null, null);
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameContainsDigits() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john1", null, null);
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameIsTooShort() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("ab", null, null);
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldFailWhenUsernameIsTooLong() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("a".repeat(31), null, null);
            assertThat(validate(request))
                    .contains("username:Username must be 3-30 lowercase letters (a-z)");
        }

        @Test
        void shouldPassWhenUsernameIsAtMinLength() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("abc", null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenUsernameIsAtMaxLength() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("a".repeat(30), null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- bio ---

        @Test
        void shouldPassWhenBioIsNull() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldFailWhenBioIsTooLong() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", "a".repeat(501), null);
            assertThat(validate(request)).contains("bio:Bio cannot exceed 500 characters");
        }

        @Test
        void shouldPassWhenBioIsAtMaxLength() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", "a".repeat(500), null);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- avatarUrl ---

        @Test
        void shouldPassWhenAvatarUrlIsNull() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenAvatarUrlIsProvided() {
            UserProfileUpdateRequest request = new UserProfileUpdateRequest("john", null, "https://example.com/avatar.jpg");
            assertThat(validator.validate(request)).isEmpty();
        }
    }
}