package com.stokuj.books.service;

import com.stokuj.books.dto.BookPatchRequest;
import com.stokuj.books.dto.BookRequest;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.Book;
import com.stokuj.books.repository.BookRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class BookServiceTest {

    @Mock
    BookRepository bookRepository;

    @InjectMocks
    BookService bookService;

    // ========== getById ==========

    @Test
    void shouldReturnBookById() {
        // given
        var book = new Book();
        book.setId(1L);
        book.setTitle("Dune");
        book.setAuthor("Herbert");

        given(bookRepository.findById(1L)).willReturn(Optional.of(book));

        // when
        var result = bookService.getById(1L);

        // then
        assertThat(result.getTitle()).isEqualTo("Dune");
        assertThat(result.getAuthor()).isEqualTo("Herbert");
    }

    @Test
    void shouldThrowWhenBookNotFound() {
        // given
        given(bookRepository.findById(99L)).willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> bookService.getById(99L))
                .isInstanceOf(ResourceNotFoundException.class)
                .hasMessageContaining("Book not found");
    }

    // ========== getAll ==========

    @Test
    void shouldReturnAllBooks() {
        // given
        var book1 = new Book();
        book1.setTitle("Dune");

        var book2 = new Book();
        book2.setTitle("Foundation");

        given(bookRepository.findAll()).willReturn(List.of(book1, book2));

        // when
        var result = bookService.getAll();

        // then
        assertThat(result).hasSize(2);
        assertThat(result).extracting(Book::getTitle)
                .containsExactly("Dune", "Foundation");
    }

    @Test
    void shouldReturnEmptyListWhenNoBooksExist() {
        // given
        given(bookRepository.findAll()).willReturn(List.of());

        // when
        var result = bookService.getAll();

        // then
        assertThat(result).isEmpty();
    }

    // ========== create ==========

    @Test
    void shouldCreateBookFromRequest() {
        // given
        var request = new BookRequest();
        request.setTitle("Dune");
        request.setAuthor("Herbert");
        request.setYear(1965);
        request.setIsbn("978-0441013593");
        request.setGenres(Set.of("Sci-Fi"));

        var savedBook = new Book();
        savedBook.setId(1L);
        savedBook.setTitle("Dune");
        savedBook.setAuthor("Herbert");

        given(bookRepository.save(any(Book.class))).willReturn(savedBook);

        // when
        var result = bookService.create(request);

        // then
        assertThat(result.getId()).isEqualTo(1L);
        assertThat(result.getTitle()).isEqualTo("Dune");
        verify(bookRepository).save(any(Book.class));
    }

    // ========== update ==========

    @Test
    void shouldUpdateExistingBook() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Old Title");

        var request = new BookRequest();
        request.setTitle("Dune");
        request.setAuthor("Herbert");
        request.setYear(1965);

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.update(1L, request);

        // then
        assertThat(result.getTitle()).isEqualTo("Dune");
        assertThat(result.getAuthor()).isEqualTo("Herbert");
        verify(bookRepository).save(existing);
    }

    @Test
    void shouldThrowWhenUpdatingNonExistentBook() {
        // given
        given(bookRepository.findById(99L)).willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> bookService.update(99L, new BookRequest()))
                .isInstanceOf(ResourceNotFoundException.class);

        verify(bookRepository, never()).save(any());
    }

    // ========== patch ==========

    @Test
    void shouldPatchOnlyProvidedFields() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Old Title");
        existing.setAuthor("Old Author");

        var patchRequest = new BookPatchRequest();
        patchRequest.setTitle("New Title");
        // author = null → nie powinien być nadpisany

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, patchRequest);

        // then
        assertThat(result.getTitle()).isEqualTo("New Title");
        assertThat(result.getAuthor()).isEqualTo("Old Author"); // niezmieniony!
    }

    // ========== delete ==========

    @Test
    void shouldDeleteBookById() {
        // when
        bookService.delete(1L);

        // then
        verify(bookRepository).deleteById(1L);
    }
}