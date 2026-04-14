package com.stokuj.books.author;

import com.stokuj.books.author.dto.AuthorRequest;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.Set;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

public class AuthorDtoTest {


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
    // AuthorRequest
    // -------------------------------------------------------------------------

    // --- happy path ---

    @Test
    void shouldPassWhenOnlyRequiredFieldIsProvided() {
        AuthorRequest request = new AuthorRequest("John Doe", null, null);
        assertThat(validator.validate(request)).isEmpty();
    }

    @Test
    void shouldPassWhenAllFieldsAreValid() {
        AuthorRequest request = new AuthorRequest("John Doe", "A short biography of the author.", LocalDate.of(1980, 1, 1)
        );
        assertThat(validator.validate(request)).isEmpty();
    }

    // --- name ---

    @Test
    void shouldFailWhenNameIsBlank() {
        AuthorRequest request = new AuthorRequest("", null, null);
        assertThat(validate(request)).contains("name:Author name is required");
    }

    @Test
    void shouldFailWhenNameIsTooShort() {
        AuthorRequest request = new AuthorRequest("ab", null, null);
        assertThat(validate(request))
                .contains("name:Name must be between 6 and 80 characters long");
    }

    @Test
    void shouldFailWhenNameIsTooLong() {
        AuthorRequest request = new AuthorRequest("a".repeat(81), null, null);
        assertThat(validate(request))
                .contains("name:Name must be between 6 and 80 characters long");
    }

    @Test
    void shouldPassWhenNameIsAtMinLength() {
        AuthorRequest request = new AuthorRequest("abc", null, null);
        assertThat(validator.validate(request)).isEmpty();
    }

    @Test
    void shouldPassWhenNameIsAtMaxLength() {
        AuthorRequest request = new AuthorRequest("a".repeat(80), null, null);
        assertThat(validator.validate(request)).isEmpty();
    }

    // --- bio ---

    @Test
    void shouldPassWhenBioIsNull() {
        AuthorRequest request = new AuthorRequest("John Doe", null, null);
        assertThat(validator.validate(request)).isEmpty();
    }

    @Test
    void shouldFailWhenBioIsTooShort() {
        AuthorRequest request = new AuthorRequest("John Doe", "Too short", null);
        assertThat(validate(request))
                .contains("bio:Name must be between 10 and 160 characters long");
    }

    @Test
    void shouldFailWhenBioIsTooLong() {
        AuthorRequest request = new AuthorRequest("John Doe", "a".repeat(161), null);
        assertThat(validate(request))
                .contains("bio:Name must be between 10 and 160 characters long");
    }

    @Test
    void shouldPassWhenBioIsAtMinLength() {
        AuthorRequest request = new AuthorRequest("John Doe", "a".repeat(10), null);
        assertThat(validator.validate(request)).isEmpty();
    }

    @Test
    void shouldPassWhenBioIsAtMaxLength() {
        AuthorRequest request = new AuthorRequest("John Doe", "a".repeat(160), null);
        assertThat(validator.validate(request)).isEmpty();
    }

}