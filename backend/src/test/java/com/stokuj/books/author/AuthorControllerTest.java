package com.stokuj.books.author;

import com.stokuj.books.author.dto.AuthorRequest;
import com.stokuj.books.author.dto.AuthorResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
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

import java.lang.reflect.Field;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;

@ExtendWith(MockitoExtension.class)
class AuthorControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    AuthorRepository authorRepository;

    @InjectMocks
    AuthorController authorController;

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
    class GetAll {

        @Test
        void shouldReturnAllAuthors() {
            Author a1 = author(1L, "Frank Herbert", "Sci-fi author", LocalDate.of(1920, 10, 8));
            Author a2 = author(2L, "Isaac Asimov", "Foundation author", LocalDate.of(1920, 1, 2));
            given(authorRepository.findAll()).willReturn(List.of(a1, a2));

            ResponseEntity<List<AuthorResponse>> response = authorController.getAll();

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
            assertThat(response.getBody().get(0).name()).isEqualTo("Frank Herbert");
            assertThat(response.getBody().get(1).name()).isEqualTo("Isaac Asimov");
        }

        @Test
        void shouldReturnEmptyListWhenNoAuthors() {
            given(authorRepository.findAll()).willReturn(List.of());

            ResponseEntity<List<AuthorResponse>> response = authorController.getAll();

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEmpty();
        }
    }

    @Nested
    class GetById {

        @Test
        void shouldReturnAuthorById() {
            Author author = author(1L, "Frank Herbert", "Sci-fi author", LocalDate.of(1920, 10, 8));
            given(authorRepository.findById(1L)).willReturn(Optional.of(author));

            ResponseEntity<AuthorResponse> response = authorController.getById(1L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().id()).isEqualTo(1L);
            assertThat(response.getBody().name()).isEqualTo("Frank Herbert");
        }

        @Test
        void shouldThrowWhenAuthorNotFound() {
            given(authorRepository.findById(404L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> authorController.getById(404L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Author not found");
        }
    }

    @Nested
    class Create {

        @Test
        void shouldCreateAuthor() {
            AuthorRequest request = new AuthorRequest("Frank Herbert", "Sci-fi author", LocalDate.of(1920, 10, 8));
            Author saved = author(1L, "Frank Herbert", "Sci-fi author", LocalDate.of(1920, 10, 8));
            given(authorRepository.save(org.mockito.ArgumentMatchers.any(Author.class))).willReturn(saved);

            ResponseEntity<AuthorResponse> response = authorController.create(request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().id()).isEqualTo(1L);
            assertThat(response.getBody().name()).isEqualTo("Frank Herbert");
        }

        @Test
        void shouldHaveValidationViolationsForInvalidPayload() {
            AuthorRequest invalid = new AuthorRequest("A", "short", LocalDate.of(2000, 1, 1));

            Set<ConstraintViolation<AuthorRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("name"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("bio"));
        }
    }

    @Nested
    class Update {

        @Test
        void shouldUpdateExistingAuthor() {
            Author existing = author(1L, "Old Name", "Old bio text", LocalDate.of(1980, 1, 1));
            AuthorRequest request = new AuthorRequest("New Name", "New bio text long", LocalDate.of(1970, 6, 15));
            Author saved = author(1L, "New Name", "New bio text long", LocalDate.of(1970, 6, 15));

            given(authorRepository.findById(1L)).willReturn(Optional.of(existing));
            given(authorRepository.save(existing)).willReturn(saved);

            ResponseEntity<AuthorResponse> response = authorController.update(1L, request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isNotNull();
            assertThat(response.getBody().name()).isEqualTo("New Name");
            assertThat(response.getBody().bio()).isEqualTo("New bio text long");
        }

        @Test
        void shouldThrowWhenUpdatingMissingAuthor() {
            AuthorRequest request = new AuthorRequest("New Name", "New bio text long", LocalDate.of(1970, 6, 15));
            given(authorRepository.findById(404L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> authorController.update(404L, request))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Author not found");
        }
    }

    @Nested
    class Delete {

        @Test
        void shouldDeleteAuthorAndReturnNoContent() {
            ResponseEntity<Void> response = authorController.delete(1L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }
    }

    private Author author(Long id, String name, String bio, LocalDate birthDate) {
        Author author = new Author();
        setField(author, "id", id);
        setField(author, "name", name);
        setField(author, "bio", bio);
        setField(author, "birthDate", birthDate);
        return author;
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
