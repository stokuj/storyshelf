package com.stokuj.books.book.book;

import com.stokuj.books.book.book.dto.BookDetailResponse;
import com.stokuj.books.book.book.dto.BookPatchRequest;
import com.stokuj.books.book.book.dto.BookRequest;
import com.stokuj.books.book.book.dto.BookResponse;
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
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.List;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class BookControllerTest {

    private static ValidatorFactory validatorFactory;
    private static Validator validator;

    @Mock
    BookService bookService;

    @Mock
    BookDetailService bookDetailService;

    @Mock
    Authentication authentication;

    @InjectMocks
    BookController bookController;

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
    class Search {

        @Test
        void shouldSearchBooks() {
            List<BookResponse> books = List.of(bookResponse(1L, "Dune"), bookResponse(2L, "Foundation"));
            given(bookService.search("du")).willReturn(books);

            ResponseEntity<List<BookResponse>> response = bookController.search("du");

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).hasSize(2);
        }
    }

    @Nested
    class GetById {

        @Test
        void shouldReturnBookById() {
            BookResponse book = bookResponse(10L, "Dune");
            given(bookService.getById(10L)).willReturn(book);

            ResponseEntity<BookResponse> response = bookController.getById(10L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(book);
        }
    }

    @Nested
    class Details {

        @Test
        void shouldReturnDetailsForAnonymousUser() {
            BookDetailResponse details = new BookDetailResponse(
                    bookResponse(1L, "Dune"),
                    new BookDetailResponse.AnalysisStatusResponse(5, 3, false),
                    null,
                    List.of(),
                    List.of(),
                    List.of(),
                    List.of()
            );
            given(bookDetailService.getById(1L, null)).willReturn(details);

            ResponseEntity<BookDetailResponse> response = bookController.getDetails(1L, null);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(details);
        }

        @Test
        void shouldReturnDetailsForAnonymousAuthenticationToken() {
            Authentication anonymous = new AnonymousAuthenticationToken(
                    "key",
                    "anonymousUser",
                    List.of(new SimpleGrantedAuthority("ROLE_ANONYMOUS"))
            );
            BookDetailResponse details = new BookDetailResponse(
                    bookResponse(1L, "Dune"),
                    new BookDetailResponse.AnalysisStatusResponse(5, 5, true),
                    null,
                    List.of(),
                    List.of(),
                    List.of(),
                    List.of()
            );
            given(bookDetailService.getById(1L, null)).willReturn(details);

            ResponseEntity<BookDetailResponse> response = bookController.getDetails(1L, anonymous);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(details);
        }

        @Test
        void shouldReturnDetailsForAuthenticatedUser() {
            given(authentication.isAuthenticated()).willReturn(true);
            given(authentication.getName()).willReturn("john@example.com");
            BookDetailResponse details = new BookDetailResponse(
                    bookResponse(1L, "Dune"),
                    new BookDetailResponse.AnalysisStatusResponse(5, 5, true),
                    null,
                    List.of(),
                    List.of(),
                    List.of(),
                    List.of()
            );
            given(bookDetailService.getById(1L, "john@example.com")).willReturn(details);

            ResponseEntity<BookDetailResponse> response = bookController.getDetails(1L, authentication);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(details);
        }
    }

    @Nested
    class WriteOperations {

        @Test
        void shouldCreateBook() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, Set.of("Sci-Fi"), Set.of("classic"));
            BookResponse created = bookResponse(1L, "Dune");
            given(bookService.create(request)).willReturn(created);

            ResponseEntity<BookResponse> response = bookController.create(request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(response.getBody()).isEqualTo(created);
        }

        @Test
        void shouldUpdateBook() {
            BookRequest request = new BookRequest("Dune", 1L, 1965, null, null, 412, Set.of("Sci-Fi"), Set.of("classic"));
            BookResponse updated = bookResponse(1L, "Dune");
            given(bookService.update(1L, request)).willReturn(updated);

            ResponseEntity<BookResponse> response = bookController.update(1L, request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(updated);
        }

        @Test
        void shouldPatchBook() {
            BookPatchRequest request = new BookPatchRequest("Dune 2", 1L, null, null, null, null, null, null);
            BookResponse patched = bookResponse(1L, "Dune 2");
            given(bookService.patch(1L, request)).willReturn(patched);

            ResponseEntity<BookResponse> response = bookController.patch(1L, request);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(response.getBody()).isEqualTo(patched);
        }

        @Test
        void shouldDeleteBook() {
            ResponseEntity<Void> response = bookController.delete(1L);

            assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
            verify(bookService).delete(1L);
        }
    }

    @Nested
    class RequestValidation {

        @Test
        void shouldHaveValidationViolationsForInvalidBookRequest() {
            BookRequest invalid = new BookRequest("", null, 0, null, null, 0, Set.of(), Set.of());

            Set<ConstraintViolation<BookRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("title"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("authorId"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("year"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("pageCount"));
        }

        @Test
        void shouldHaveValidationViolationsForInvalidBookPatchRequest() {
            BookPatchRequest invalid = new BookPatchRequest("x".repeat(300), null, -1, null, null, -1, null, null);

            Set<ConstraintViolation<BookPatchRequest>> violations = validator.validate(invalid);

            assertThat(violations).isNotEmpty();
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("title"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("year"));
            assertThat(violations).anyMatch(v -> v.getPropertyPath().toString().equals("pageCount"));
        }
    }

    private BookResponse bookResponse(Long id, String title) {
        return new BookResponse(id, title, "Author", 2000, null, null, 300, Set.of("Fiction"), List.of("classic"), 4.5, 10);
    }
}
