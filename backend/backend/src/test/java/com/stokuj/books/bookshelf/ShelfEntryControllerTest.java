package com.stokuj.books.bookshelf;

import com.stokuj.books.bookshelf.dto.ShelfEntryRequest;
import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ShelfEntryControllerTest {

    @Mock
    ShelfEntryService shelfEntryService;

    @Mock
    Authentication authentication;

    @InjectMocks
    ShelfEntryController shelfEntryController;

    @Nested
    class GetMyBooks {

        @Test
        void shouldReturnMyBooks() {
            given(authentication.getName()).willReturn("john@example.com");
            List<ShelfEntryResponse> entries = List.of(response(1L, "Dune", ReadingStatus.READING));
            given(shelfEntryService.getMyBooks("john@example.com")).willReturn(entries);

            ResponseEntity<List<ShelfEntryResponse>> result = shelfEntryController.getMyBooks(authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).hasSize(1);
            assertThat(result.getBody().get(0).book().title()).isEqualTo("Dune");
            verify(shelfEntryService).getMyBooks("john@example.com");
        }
    }

    @Nested
    class AddToShelf {

        @Test
        void shouldAddBookToShelfAndReturnCreated() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryRequest request = new ShelfEntryRequest(ReadingStatus.READ);
            ShelfEntryResponse expected = response(2L, "Foundation", ReadingStatus.READ);
            given(shelfEntryService.addToShelf("john@example.com", 2L, request)).willReturn(expected);

            ResponseEntity<ShelfEntryResponse> result = shelfEntryController.addToShelf(2L, request, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(result.getBody()).isEqualTo(expected);
        }

        @Test
        void shouldAddBookToShelfWithNullRequest() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryResponse expected = response(3L, "Hyperion", ReadingStatus.WANT_TO_READ);
            given(shelfEntryService.addToShelf("john@example.com", 3L, null)).willReturn(expected);

            ResponseEntity<ShelfEntryResponse> result = shelfEntryController.addToShelf(3L, null, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(result.getBody()).isEqualTo(expected);
        }

        @Test
        void shouldPropagateConflictWhenBookAlreadyOnShelf() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryRequest request = new ShelfEntryRequest(ReadingStatus.READING);
            given(shelfEntryService.addToShelf("john@example.com", 4L, request))
                    .willThrow(new ConflictException("This book is already on your shelf"));

            assertThatThrownBy(() -> shelfEntryController.addToShelf(4L, request, authentication))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("This book is already on your shelf");
        }
    }

    @Nested
    class GetShelfEntry {

        @Test
        void shouldReturnShelfEntryWhenPresent() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryResponse expected = response(5L, "Mistborn", ReadingStatus.READING);
            given(shelfEntryService.findByUserAndBook("john@example.com", 5L)).willReturn(Optional.of(expected));

            ResponseEntity<ShelfEntryResponse> result = shelfEntryController.getShelfEntry(5L, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(expected);
        }

        @Test
        void shouldReturnNotFoundWhenShelfEntryMissing() {
            given(authentication.getName()).willReturn("john@example.com");
            given(shelfEntryService.findByUserAndBook("john@example.com", 99L)).willReturn(Optional.empty());

            ResponseEntity<ShelfEntryResponse> result = shelfEntryController.getShelfEntry(99L, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
            assertThat(result.getBody()).isNull();
        }
    }

    @Nested
    class UpdateStatus {

        @Test
        void shouldUpdateStatusAndReturnOk() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryRequest request = new ShelfEntryRequest(ReadingStatus.READ);
            ShelfEntryResponse expected = response(6L, "Neuromancer", ReadingStatus.READ);
            given(shelfEntryService.updateStatus("john@example.com", 6L, request)).willReturn(expected);

            ResponseEntity<ShelfEntryResponse> result = shelfEntryController.updateStatus(6L, request, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(result.getBody()).isEqualTo(expected);
        }

        @Test
        void shouldPropagateNotFoundWhenUpdatingMissingEntry() {
            given(authentication.getName()).willReturn("john@example.com");
            ShelfEntryRequest request = new ShelfEntryRequest(ReadingStatus.READING);
            given(shelfEntryService.updateStatus("john@example.com", 404L, request))
                    .willThrow(new ResourceNotFoundException("Book is not on your shelf"));

            assertThatThrownBy(() -> shelfEntryController.updateStatus(404L, request, authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book is not on your shelf");
        }
    }

    @Nested
    class RemoveFromShelf {

        @Test
        void shouldRemoveBookAndReturnNoContent() {
            given(authentication.getName()).willReturn("john@example.com");

            ResponseEntity<Void> result = shelfEntryController.removeFromShelf(7L, authentication);

            assertThat(result.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
            verify(shelfEntryService).removeFromShelf("john@example.com", 7L);
        }

        @Test
        void shouldPropagateNotFoundWhenRemovingMissingEntry() {
            given(authentication.getName()).willReturn("john@example.com");
            org.mockito.Mockito.doThrow(new ResourceNotFoundException("Book is not on your shelf"))
                    .when(shelfEntryService)
                    .removeFromShelf("john@example.com", 8L);

            assertThatThrownBy(() -> shelfEntryController.removeFromShelf(8L, authentication))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book is not on your shelf");
        }
    }

    private ShelfEntryResponse response(Long bookId, String title, ReadingStatus status) {
        return new ShelfEntryResponse(
                new ShelfEntryResponse.BookSummary(bookId, title, "Author"),
                status,
                Instant.now()
        );
    }
}
