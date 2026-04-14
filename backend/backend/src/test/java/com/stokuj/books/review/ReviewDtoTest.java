package com.stokuj.books.review;

import com.stokuj.books.review.dto.ReviewRequest;
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

class ReviewDtoTest {

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
    class ReviewRequestTests {

        private static final String VALID_CONTENT = "This is a valid review content.";

        // --- happy path ---

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            ReviewRequest request = new ReviewRequest(3, VALID_CONTENT);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- rating ---

        @Test
        void shouldFailWhenRatingIsTooLow() {
            ReviewRequest request = new ReviewRequest(0, VALID_CONTENT);
            assertThat(validate(request)).contains("rating:Rating must be at least 1");
        }

        @Test
        void shouldFailWhenRatingIsTooHigh() {
            ReviewRequest request = new ReviewRequest(6, VALID_CONTENT);
            assertThat(validate(request)).contains("rating:Rating must not exceed 5");
        }

        @Test
        void shouldPassWhenRatingIsAtMin() {
            ReviewRequest request = new ReviewRequest(1, VALID_CONTENT);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenRatingIsAtMax() {
            ReviewRequest request = new ReviewRequest(5, VALID_CONTENT);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- content ---

        @Test
        void shouldFailWhenContentIsBlank() {
            ReviewRequest request = new ReviewRequest(3, "");
            assertThat(validate(request)).contains("content:Review content cannot be empty");
        }

        @Test
        void shouldFailWhenContentIsTooShort() {
            ReviewRequest request = new ReviewRequest(3, "Too short");
            assertThat(validate(request))
                    .contains("content:Review must be between 10 and 2000 characters long");
        }

        @Test
        void shouldFailWhenContentIsTooLong() {
            ReviewRequest request = new ReviewRequest(3, "a".repeat(2001));
            assertThat(validate(request))
                    .contains("content:Review must be between 10 and 2000 characters long");
        }

        @Test
        void shouldPassWhenContentIsAtMinLength() {
            ReviewRequest request = new ReviewRequest(3, "a".repeat(10));
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenContentIsAtMaxLength() {
            ReviewRequest request = new ReviewRequest(3, "a".repeat(2000));
            assertThat(validator.validate(request)).isEmpty();
        }
    }
}