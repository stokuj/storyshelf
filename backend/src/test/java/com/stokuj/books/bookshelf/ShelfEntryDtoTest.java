package com.stokuj.books.bookshelf;

import com.stokuj.books.bookshelf.ReadingStatus;
import com.stokuj.books.bookshelf.dto.ShelfEntryRequest;
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

class ShelfEntryRequestDtoTest {

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
    class ShelfEntryRequestTests {

        @Test
        void shouldPassForEachValidStatus() {
            for (ReadingStatus status : ReadingStatus.values()) {
                ShelfEntryRequest request = new ShelfEntryRequest(status);
                assertThat(validator.validate(request))
                        .as("Expected no violations for status: %s", status)
                        .isEmpty();
            }
        }

        @Test
        void shouldFailWhenStatusIsNull() {
            ShelfEntryRequest request = new ShelfEntryRequest(null);
            assertThat(validate(request)).contains("status:Status is required");
        }
    }
}