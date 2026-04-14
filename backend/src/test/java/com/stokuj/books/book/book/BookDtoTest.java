package com.stokuj.books.book.book;

import com.stokuj.books.book.book.dto.BookPatchRequest;
import com.stokuj.books.book.book.dto.BookRequest;
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

class BookDtoTest {

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
    // BookRequest
    // -------------------------------------------------------------------------

    @Nested
    class BookRequestTests {

        @Test
        void shouldPassWhenAllRequiredFieldsAreValid() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenOptionalFieldsAreNull() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldDefaultGenresToEmptySetWhenNull() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, null, null);
            assertThat(request.genres()).isNotNull().isEmpty();
        }

        @Test
        void shouldDefaultTagIdsToEmptySetWhenNull() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, null, null);
            assertThat(request.tagIds()).isNotNull().isEmpty();
        }

        // --- title ---

        @Test
        void shouldFailWhenTitleIsBlank() {
            BookRequest request = new BookRequest("", 1L, 1965, null, null, 412, null, null);
            assertThat(validate(request)).contains("title:Title is required");
        }

        // --- authorId ---

        @Test
        void shouldFailWhenAuthorIdIsNull() {
            BookRequest request = new BookRequest("Dune", null, 1965, null, null, 412, null, null);
            assertThat(validate(request)).contains("authorId:Author is required");
        }

        // --- year ---

        @Test
        void shouldFailWhenYearIsZero() {
            BookRequest request = new BookRequest("Dune", 1L, 0, null, null, 412, null, null);
            assertThat(validate(request)).contains("year:Year must be a positive number");
        }

        @Test
        void shouldFailWhenYearIsNegative() {
            BookRequest request = new BookRequest("Dune", 1L, -1, null, null, 412, null, null);
            assertThat(validate(request)).contains("year:Year must be a positive number");
        }

        @Test
        void shouldPassWhenYearIsOne() {
            BookRequest request = new BookRequest("Dune", 1L, 1, null, null, 412, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- pageCount ---

        @Test
        void shouldFailWhenPageCountIsZero() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 0, null, null);
            assertThat(validate(request)).contains("pageCount:Page count must be positive");
        }

        @Test
        void shouldFailWhenPageCountIsNegative() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, -1, null, null);
            assertThat(validate(request)).contains("pageCount:Page count must be positive");
        }

        @Test
        void shouldPassWhenPageCountIsOne() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 1, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }
    }

    // -------------------------------------------------------------------------
    // BookPatchRequest
    // -------------------------------------------------------------------------

    @Nested
    class BookPatchRequestTests {

        @Test
        void shouldPassWhenAllFieldsAreNull() {
            BookPatchRequest request = new BookPatchRequest(null, null, null, null, null, null, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        @Test
        void shouldPassWhenAllFieldsAreValid() {
            BookPatchRequest request = new BookPatchRequest("Dune", 1L, 1965, "978-0441013593", "A great book.", 412, Set.of("sci-fi"), Set.of(1L));
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- title ---

        @Test
        void shouldFailWhenTitleIsTooLong() {
            BookPatchRequest request = new BookPatchRequest("a".repeat(256), null, null, null, null, null, null, null);
            assertThat(validate(request)).contains("title:Title is too long");
        }

        @Test
        void shouldPassWhenTitleIsAtMaxLength() {
            BookPatchRequest request = new BookPatchRequest("a".repeat(255), null, null, null, null, null, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- year ---

        @Test
        void shouldFailWhenYearIsNegative() {
            BookPatchRequest request = new BookPatchRequest(null, null, -1, null, null, null, null, null);
            assertThat(validate(request)).contains("year:Year must be positive");
        }

        @Test
        void shouldPassWhenYearIsNull() {
            BookPatchRequest request = new BookPatchRequest(null, null, null, null, null, null, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }

        // --- pageCount ---

        @Test
        void shouldFailWhenPageCountIsNegative() {
            BookPatchRequest request = new BookPatchRequest(null, null, null, null, null, -1, null, null);
            assertThat(validate(request)).contains("pageCount:Page count must be positive");
        }

        @Test
        void shouldPassWhenPageCountIsNull() {
            BookPatchRequest request = new BookPatchRequest(null, null, null, null, null, null, null, null);
            assertThat(validator.validate(request)).isEmpty();
        }
    }
}