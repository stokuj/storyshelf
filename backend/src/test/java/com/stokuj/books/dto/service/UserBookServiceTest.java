package com.stokuj.books.dto.service;

import com.stokuj.books.dto.UserBookRequest;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.enums.ReadingStatus;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.domain.entity.Bookshelf;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.UserBookRepository;
import com.stokuj.books.repository.UserRepository;
import com.stokuj.books.service.UserBookService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class UserBookServiceTest {

    @Mock
    UserBookRepository userBookRepository;

    @Mock
    UserRepository userRepository;

    @Mock
    BookRepository bookRepository;

    @InjectMocks
    UserBookService userBookService;

    // ========== helpers ==========

    private User makeUser(String email) {
        var user = new User();
        user.setId(1L);
        user.setEmail(email);
        return user;
    }

    private Book makeBook(Long id, String title) {
        var book = new Book();
        book.setId(id);
        book.setTitle(title);
        book.setAuthor("Herbert");
        return book;
    }

    private Bookshelf makeUserBook(User user, Book book, ReadingStatus status) {
        var ub = new Bookshelf();
        ub.setUser(user);
        ub.setBook(book);
        ub.setStatus(status);
        ub.setCreatedAt(Instant.now());
        return ub;
    }

    // ========== getMyBooks ==========

    @Test
    void shouldReturnAllBooksForUser() {
        // given
        var user = makeUser("user@test.com");
        var book1 = makeBook(1L, "Dune");
        var book2 = makeBook(2L, "Foundation");

        var userBooks = List.of(
                makeUserBook(user, book1, ReadingStatus.READING),
                makeUserBook(user, book2, ReadingStatus.WANT_TO_READ)
        );

        given(userBookRepository.findAllByUserEmailOrderByCreatedAtDesc("user@test.com"))
                .willReturn(userBooks);

        // when
        var result = userBookService.getMyBooks("user@test.com");

        // then
        assertThat(result).hasSize(2);
        assertThat(result).extracting(r -> r.getBook().getTitle())
                .containsExactly("Dune", "Foundation");
    }

    @Test
    void shouldReturnEmptyListWhenUserHasNoBooks() {
        // given
        given(userBookRepository.findAllByUserEmailOrderByCreatedAtDesc("user@test.com"))
                .willReturn(List.of());

        // when
        var result = userBookService.getMyBooks("user@test.com");

        // then
        assertThat(result).isEmpty();
    }

    // ========== findByUserAndBook ==========

    @Test
    void shouldReturnUserBookWhenExists() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");
        var userBook = makeUserBook(user, book, ReadingStatus.READING);

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.of(userBook));

        // when
        var result = userBookService.findByUserAndBook("user@test.com", 1L);

        // then
        assertThat(result).isPresent();
        assertThat(result.get().getStatus()).isEqualTo(ReadingStatus.READING);
    }

    @Test
    void shouldReturnEmptyWhenUserBookDoesNotExist() {
        // given
        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 99L))
                .willReturn(Optional.empty());

        // when
        var result = userBookService.findByUserAndBook("user@test.com", 99L);

        // then
        assertThat(result).isEmpty();
    }

    // ========== addToShelf ==========

    @Test
    void shouldAddBookToShelfWithDefaultStatus() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.empty());
        given(userRepository.findByEmail("user@test.com"))
                .willReturn(Optional.of(user));
        given(bookRepository.findById(1L))
                .willReturn(Optional.of(book));
        given(userBookRepository.save(any(Bookshelf.class)))
                .willAnswer(inv -> inv.getArgument(0));

        // when
        var result = userBookService.addToShelf("user@test.com", 1L, null);

        // then
        assertThat(result.getStatus()).isEqualTo(ReadingStatus.WANT_TO_READ);
        assertThat(result.getBook().getTitle()).isEqualTo("Dune");
        verify(userBookRepository).save(any(Bookshelf.class));
    }

    @Test
    void shouldAddBookToShelfWithRequestedStatus() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");

        var request = new UserBookRequest();
        request.setStatus(ReadingStatus.READING);

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.empty());
        given(userRepository.findByEmail("user@test.com"))
                .willReturn(Optional.of(user));
        given(bookRepository.findById(1L))
                .willReturn(Optional.of(book));
        given(userBookRepository.save(any(Bookshelf.class)))
                .willAnswer(inv -> inv.getArgument(0));

        // when
        var result = userBookService.addToShelf("user@test.com", 1L, request);

        // then
        assertThat(result.getStatus()).isEqualTo(ReadingStatus.READING);
        assertThat(result.getBook().getTitle()).isEqualTo("Dune");
    }

    @Test
    void shouldThrowConflictWhenBookAlreadyOnShelf() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.of(makeUserBook(user, book, ReadingStatus.READING)));

        // when / then
        assertThatThrownBy(() -> userBookService.addToShelf("user@test.com", 1L, null))
                .isInstanceOf(ConflictException.class)
                .hasMessageContaining("juz na polce");

        verify(userBookRepository, never()).save(any());
    }

    @Test
    void shouldThrowWhenUserNotFoundOnAdd() {
        // given
        given(userBookRepository.findByUserEmailAndBookId("ghost@test.com", 1L))
                .willReturn(Optional.empty());
        given(userRepository.findByEmail("ghost@test.com"))
                .willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> userBookService.addToShelf("ghost@test.com", 1L, null))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("User not found");
    }

    @Test
    void shouldThrowWhenBookNotFoundOnAdd() {
        // given
        var user = makeUser("user@test.com");

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 99L))
                .willReturn(Optional.empty());
        given(userRepository.findByEmail("user@test.com"))
                .willReturn(Optional.of(user));
        given(bookRepository.findById(99L))
                .willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> userBookService.addToShelf("user@test.com", 99L, null))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Book not found");
    }

    // ========== updateStatus ==========

    @Test
    void shouldUpdateBookStatus() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");
        var userBook = makeUserBook(user, book, ReadingStatus.WANT_TO_READ);

        var request = new UserBookRequest();
        request.setStatus(ReadingStatus.READ);

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.of(userBook));
        given(userBookRepository.save(any(Bookshelf.class)))
                .willAnswer(inv -> inv.getArgument(0));

        // when
        var result = userBookService.updateStatus("user@test.com", 1L, request);

        // then
        assertThat(result.getStatus()).isEqualTo(ReadingStatus.READ);
        verify(userBookRepository).save(userBook);
    }

    @Test
    void shouldThrowWhenBookNotOnShelfOnUpdate() {
        // given
        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 99L))
                .willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> userBookService.updateStatus("user@test.com", 99L, new UserBookRequest()))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("not on your shelf");
    }

    @Test
    void shouldThrowWhenStatusIsNullOnUpdate() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");
        var userBook = makeUserBook(user, book, ReadingStatus.READING);

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.of(userBook));

        // when / then
        assertThatThrownBy(() -> userBookService.updateStatus("user@test.com", 1L, null))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Status is required");

        verify(userBookRepository, never()).save(any());
    }

    // ========== removeFromShelf ==========

    @Test
    void shouldRemoveBookFromShelf() {
        // given
        var user = makeUser("user@test.com");
        var book = makeBook(1L, "Dune");
        var userBook = makeUserBook(user, book, ReadingStatus.READING);

        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 1L))
                .willReturn(Optional.of(userBook));

        // when
        userBookService.removeFromShelf("user@test.com", 1L);

        // then
        verify(userBookRepository).delete(userBook);
    }

    @Test
    void shouldThrowWhenRemovingBookNotOnShelf() {
        // given
        given(userBookRepository.findByUserEmailAndBookId("user@test.com", 99L))
                .willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> userBookService.removeFromShelf("user@test.com", 99L))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("not on your shelf");

        verify(userBookRepository, never()).delete(any());
    }
}