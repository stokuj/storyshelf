package com.stokuj.books.bookshelf;

import com.stokuj.books.book.book.Book;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.bookshelf.dto.ShelfEntryRequest;
import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class ShelfEntryServiceTest {

    @Mock
    ShelfEntryRepository shelfEntryRepository;

    @Mock
    UserRepository userRepository;

    @Mock
    BookRepository bookRepository;

    @InjectMocks
    ShelfEntryService shelfEntryService;

    @Nested
    class GetMyBooks {

        @Test
        void shouldReturnMyBooksMappedToResponse() {
            // given: repository returns two shelf entries for the user
            ShelfEntry first = shelfEntry(user("john@example.com"), book(1L, "Dune", "Frank Herbert"), ReadingStatus.READING);
            ShelfEntry second = shelfEntry(user("john@example.com"), book(2L, "Foundation", "Isaac Asimov"), ReadingStatus.READ);
            setField(first, "createdAt", Instant.parse("2024-01-01T10:00:00Z"));
            setField(second, "createdAt", Instant.parse("2024-01-02T10:00:00Z"));
            given(shelfEntryRepository.findAllByUserEmailOrderByCreatedAtDesc("john@example.com"))
                    .willReturn(List.of(second, first));

            // when: getMyBooks is called
            List<ShelfEntryResponse> result = shelfEntryService.getMyBooks("john@example.com");

            // then: service maps entries to response DTOs
            assertThat(result).hasSize(2);
            assertThat(result.get(0).book().id()).isEqualTo(2L);
            assertThat(result.get(0).book().title()).isEqualTo("Foundation");
            assertThat(result.get(0).status()).isEqualTo(ReadingStatus.READ);
            assertThat(result.get(1).book().id()).isEqualTo(1L);
            assertThat(result.get(1).status()).isEqualTo(ReadingStatus.READING);
        }
    }

    @Nested
    class FindByUserAndBook {

        @Test
        void shouldReturnShelfEntryWhenExists() {
            // given: repository returns shelf entry for user/book pair
            ShelfEntry entry = shelfEntry(user("john@example.com"), book(10L, "Hyperion", "Dan Simmons"), ReadingStatus.WANT_TO_READ);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 10L)).willReturn(Optional.of(entry));

            // when: findByUserAndBook is called
            Optional<ShelfEntryResponse> result = shelfEntryService.findByUserAndBook("john@example.com", 10L);

            // then: optional response is present and correctly mapped
            assertThat(result).isPresent();
            assertThat(result.get().book().title()).isEqualTo("Hyperion");
            assertThat(result.get().status()).isEqualTo(ReadingStatus.WANT_TO_READ);
        }

        @Test
        void shouldReturnEmptyWhenShelfEntryDoesNotExist() {
            // given: repository has no shelf entry for user/book pair
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 10L)).willReturn(Optional.empty());

            // when: findByUserAndBook is called
            Optional<ShelfEntryResponse> result = shelfEntryService.findByUserAndBook("john@example.com", 10L);

            // then: optional response is empty
            assertThat(result).isEmpty();
        }
    }

    @Nested
    class AddToShelf {

        @Test
        void shouldAddBookToShelfWithProvidedStatus() {
            // given: user and book exist, and shelf entry does not yet exist
            User user = user("john@example.com");
            Book book = book(5L, "Dune", "Frank Herbert");
            ShelfEntryRequest request = new ShelfEntryRequest(ReadingStatus.READING);

            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 5L)).willReturn(Optional.empty());
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(bookRepository.findById(5L)).willReturn(Optional.of(book));

            // when: addToShelf is called with explicit status
            ShelfEntryResponse result = shelfEntryService.addToShelf("john@example.com", 5L, request);

            // then: saved shelf entry contains requested status
            ArgumentCaptor<ShelfEntry> captor = ArgumentCaptor.forClass(ShelfEntry.class);
            verify(shelfEntryRepository).save(captor.capture());
            ShelfEntry saved = captor.getValue();
            assertThat(getField(saved, "user")).isEqualTo(user);
            assertThat(getField(saved, "book")).isEqualTo(book);
            assertThat(getField(saved, "status")).isEqualTo(ReadingStatus.READING);
            assertThat(result.book().id()).isEqualTo(5L);
            assertThat(result.status()).isEqualTo(ReadingStatus.READING);
        }

        @Test
        void shouldAddBookToShelfWithDefaultStatusWhenRequestIsNull() {
            // given: user and book exist, and request is null
            User user = user("john@example.com");
            Book book = book(6L, "Foundation", "Isaac Asimov");
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 6L)).willReturn(Optional.empty());
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(bookRepository.findById(6L)).willReturn(Optional.of(book));

            // when: addToShelf is called with null request
            ShelfEntryResponse result = shelfEntryService.addToShelf("john@example.com", 6L, null);

            // then: default status WANT_TO_READ is used
            ArgumentCaptor<ShelfEntry> captor = ArgumentCaptor.forClass(ShelfEntry.class);
            verify(shelfEntryRepository).save(captor.capture());
            assertThat(getField(captor.getValue(), "status")).isEqualTo(ReadingStatus.WANT_TO_READ);
            assertThat(result.status()).isEqualTo(ReadingStatus.WANT_TO_READ);
        }

        @Test
        void shouldThrowConflictWhenBookAlreadyOnShelf() {
            // given: shelf already contains the same user/book entry
            ShelfEntry existing = shelfEntry(user("john@example.com"), book(7L, "Book", "Author"), ReadingStatus.READ);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 7L)).willReturn(Optional.of(existing));

            // when / then: service throws conflict exception
            assertThatThrownBy(() -> shelfEntryService.addToShelf("john@example.com", 7L, new ShelfEntryRequest(ReadingStatus.READ)))
                    .isInstanceOf(ConflictException.class)
                    .hasMessage("This book is already on your shelf");
        }

        @Test
        void shouldThrowWhenUserNotFoundWhileAddingToShelf() {
            // given: shelf entry does not exist, but user is missing
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 8L)).willReturn(Optional.empty());
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.empty());

            // when / then: service throws resource not found
            assertThatThrownBy(() -> shelfEntryService.addToShelf("john@example.com", 8L, new ShelfEntryRequest(ReadingStatus.READING)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("User not found");
        }

        @Test
        void shouldThrowWhenBookNotFoundWhileAddingToShelf() {
            // given: user exists, but target book is missing
            User user = user("john@example.com");
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 9L)).willReturn(Optional.empty());
            given(userRepository.findByEmail("john@example.com")).willReturn(Optional.of(user));
            given(bookRepository.findById(9L)).willReturn(Optional.empty());

            // when / then: service throws resource not found
            assertThatThrownBy(() -> shelfEntryService.addToShelf("john@example.com", 9L, new ShelfEntryRequest(ReadingStatus.READING)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }
    }

    @Nested
    class UpdateStatus {

        @Test
        void shouldUpdateStatusForExistingShelfEntry() {
            // given: shelf entry exists and request contains new status
            ShelfEntry entry = shelfEntry(user("john@example.com"), book(11L, "Book", "Author"), ReadingStatus.WANT_TO_READ);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 11L)).willReturn(Optional.of(entry));

            // when: updateStatus is called
            ShelfEntryResponse result = shelfEntryService.updateStatus(
                    "john@example.com",
                    11L,
                    new ShelfEntryRequest(ReadingStatus.READ)
            );

            // then: status is updated and saved
            verify(shelfEntryRepository).save(entry);
            assertThat(getField(entry, "status")).isEqualTo(ReadingStatus.READ);
            assertThat(result.status()).isEqualTo(ReadingStatus.READ);
        }

        @Test
        void shouldThrowWhenUpdatingMissingShelfEntry() {
            // given: shelf entry does not exist
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 12L)).willReturn(Optional.empty());

            // when / then: service throws resource not found
            assertThatThrownBy(() -> shelfEntryService.updateStatus("john@example.com", 12L, new ShelfEntryRequest(ReadingStatus.READ)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book is not on your shelf");
        }

        @Test
        void shouldThrowWhenUpdatingStatusWithNullRequest() {
            // given: shelf entry exists, but request object is null
            ShelfEntry entry = shelfEntry(user("john@example.com"), book(13L, "Book", "Author"), ReadingStatus.READING);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 13L)).willReturn(Optional.of(entry));

            // when / then: service rejects null request
            assertThatThrownBy(() -> shelfEntryService.updateStatus("john@example.com", 13L, null))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Status is required");
        }

        @Test
        void shouldThrowWhenUpdatingStatusWithNullStatus() {
            // given: shelf entry exists, but request status is null
            ShelfEntry entry = shelfEntry(user("john@example.com"), book(14L, "Book", "Author"), ReadingStatus.READING);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 14L)).willReturn(Optional.of(entry));
            ShelfEntryRequest request = new ShelfEntryRequest(null);

            // when / then: service rejects missing status value
            assertThatThrownBy(() -> shelfEntryService.updateStatus("john@example.com", 14L, request))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Status is required");
        }
    }

    @Nested
    class RemoveFromShelf {

        @Test
        void shouldRemoveShelfEntryWhenExists() {
            // given: shelf entry exists for the user/book pair
            ShelfEntry entry = shelfEntry(user("john@example.com"), book(15L, "Book", "Author"), ReadingStatus.READ);
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 15L)).willReturn(Optional.of(entry));

            // when: removeFromShelf is called
            shelfEntryService.removeFromShelf("john@example.com", 15L);

            // then: repository delete is invoked
            verify(shelfEntryRepository).delete(entry);
        }

        @Test
        void shouldThrowWhenRemovingMissingShelfEntry() {
            // given: shelf entry does not exist
            given(shelfEntryRepository.findByUserEmailAndBookId("john@example.com", 16L)).willReturn(Optional.empty());

            // when / then: service throws resource not found
            assertThatThrownBy(() -> shelfEntryService.removeFromShelf("john@example.com", 16L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book is not on your shelf");
        }
    }

    private User user(String email) {
        User user = new User();
        setField(user, "email", email);
        return user;
    }

    private Book book(Long id, String title, String authorName) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "title", title);
        setField(book, "bookAuthors", List.of());

        // This service uses Book#getAuthor(); overriding with empty authors would return null,
        // so we keep title/id assertions as the primary mapping checks.
        // For deterministic author mapping in this unit setup, we use reflection-backed field
        // exposed by getter logic only when available via relations.
        // Here we still set raw value for defensive compatibility.
        setField(book, "description", authorName);
        return book;
    }

    private ShelfEntry shelfEntry(User user, Book book, ReadingStatus status) {
        ShelfEntry entry = new ShelfEntry();
        setField(entry, "user", user);
        setField(entry, "book", book);
        setField(entry, "status", status);
        setField(entry, "createdAt", Instant.now());
        return entry;
    }

    private Object getField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
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
