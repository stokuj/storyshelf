package com.stokuj.books.series;

import com.stokuj.books.series.SeriesStatus;
import com.stokuj.books.series.dto.SeriesRequest;
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

class SeriesDtoTest {

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
    class SeriesRequestTests {

        private static final String VALID_NAME = "The Lord of the Rings";

        // --- happy path ---

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            SeriesRequest request = new SeriesRequest(VALID_NAME, "A great fantasy series.", SeriesStatus.ONGOING);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenDescriptionIsNull() {
            SeriesRequest request = new SeriesRequest(VALID_NAME, null, SeriesStatus.ONGOING);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- name ---

        @Test
        void shouldFailWhenNameIsBlank() {
            SeriesRequest request = new SeriesRequest("", null, SeriesStatus.ONGOING);
            assertThat(validate(request)).contains("name:Series name is required");
        }

        @Test
        void shouldFailWhenNameIsTooShort() {
            SeriesRequest request = new SeriesRequest("Short", null, SeriesStatus.ONGOING);
            assertThat(validate(request)).contains("name:Name must be between 10 and 255 characters long");
        }

        @Test
        void shouldFailWhenNameIsTooLong() {
            SeriesRequest request = new SeriesRequest("a".repeat(256), null, SeriesStatus.ONGOING);
            assertThat(validate(request)).contains("name:Name must be between 10 and 255 characters long");
        }

        @Test
        void shouldPassWhenNameIsAtMinLength() {
            SeriesRequest request = new SeriesRequest("a".repeat(10), null, SeriesStatus.ONGOING);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenNameIsAtMaxLength() {
            SeriesRequest request = new SeriesRequest("a".repeat(255), null, SeriesStatus.ONGOING);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- status ---

        @Test
        void shouldFailWhenStatusIsNull() {
            SeriesRequest request = new SeriesRequest(VALID_NAME, null, null);
            assertThat(validate(request)).contains("status:Status is required");
        }
    }
}
