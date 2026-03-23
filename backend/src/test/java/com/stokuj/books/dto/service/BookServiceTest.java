package com.stokuj.books.dto.service;

import com.stokuj.books.domain.entity.*;
import com.stokuj.books.domain.enums.AuthorRole;
import com.stokuj.books.dto.book.BookPatchRequest;
import com.stokuj.books.dto.book.BookRequest;
import com.stokuj.books.dto.book.BookResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.AuthorRepository;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.TagRepository;
import com.stokuj.books.service.BookService;
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

    @Mock
    AuthorRepository authorRepository;

    @Mock
    TagRepository tagRepository;

    @InjectMocks
    BookService bookService;

    // ========== getById ==========

    @Test
    void shouldReturnBookById() {
        // given
        var book = new Book();
        book.setId(1L);
        book.setTitle("Dune");
        book.getBookAuthors().add(makeBookAuthor(book, "Herbert"));

        given(bookRepository.findById(1L)).willReturn(Optional.of(book));

        // when
        var result = bookService.getById(1L);

        // then
        assertThat(result.title()).isEqualTo("Dune");
        assertThat(result.author()).isEqualTo("Herbert");
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
        assertThat(result).extracting(BookResponse::title)
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
        savedBook.getBookAuthors().add(makeBookAuthor(savedBook, "Herbert"));

        given(authorRepository.findByNameIgnoreCase("Herbert"))
                .willReturn(Optional.of(makeAuthor("Herbert")));

        given(bookRepository.save(any(Book.class))).willReturn(savedBook);

        // when
        var result = bookService.create(request);

        // then
        assertThat(result.id()).isEqualTo(1L);
        assertThat(result.title()).isEqualTo("Dune");
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

        given(authorRepository.findByNameIgnoreCase("Herbert"))
                .willReturn(Optional.of(makeAuthor("Herbert")));

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.update(1L, request);

        // then
        assertThat(result.title()).isEqualTo("Dune");
        assertThat(result.author()).isEqualTo("Herbert");
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
        existing.getBookAuthors().add(makeBookAuthor(existing, "Old Author"));

        var patchRequest = new BookPatchRequest();
        patchRequest.setTitle("New Title");
        // author = null → nie powinien być nadpisany

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, patchRequest);

        // then
        assertThat(result.title()).isEqualTo("New Title");
        assertThat(result.author()).isEqualTo("Old Author"); // niezmieniony!
    }

    @Test
    void shouldNotChangeAnythingWhenPatchRequestIsEmpty() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Old Title");
        existing.getBookAuthors().add(makeBookAuthor(existing, "Old Author"));
        existing.setYear(2000);

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, new BookPatchRequest()); // wszystko null

        // then
        assertThat(result.title()).isEqualTo("Old Title");
        assertThat(result.author()).isEqualTo("Old Author");
        assertThat(result.year()).isEqualTo(2000);
    }

    @Test
    void shouldPatchMultipleFieldsAtOnce() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Old Title");
        existing.getBookAuthors().add(makeBookAuthor(existing, "Old Author"));
        existing.setYear(2000);

        var request = new BookPatchRequest();
        request.setTitle("New Title");
        request.setAuthor("New Author");
        request.setYear(2024);

        given(authorRepository.findByNameIgnoreCase("New Author"))
                .willReturn(Optional.of(makeAuthor("New Author")));

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, request);

        // then
        assertThat(result.title()).isEqualTo("New Title");
        assertThat(result.author()).isEqualTo("New Author");
        assertThat(result.year()).isEqualTo(2024);
    }

    @Test
    void shouldThrowWhenPatchingNonExistentBook() {
        // given
        given(bookRepository.findById(99L)).willReturn(Optional.empty());

        // when / then
        assertThatThrownBy(() -> bookService.patch(99L, new BookPatchRequest()))
                .isInstanceOf(ResourceNotFoundException.class);

        verify(bookRepository, never()).save(any());
    }

    @Test
    void shouldPatchGenresAndTags() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Dune");
        existing.setGenres(Set.of("Sci-Fi"));
        existing.getBookTags().add(makeBookTag(existing, "classic"));

        var request = new BookPatchRequest();
        request.setGenres(Set.of("Sci-Fi", "Adventure"));
        request.setTags(List.of("classic", "must-read"));

        given(tagRepository.findByNameIgnoreCase("classic"))
                .willReturn(Optional.of(makeTag("classic")));
        given(tagRepository.findByNameIgnoreCase("must-read"))
                .willReturn(Optional.of(makeTag("must-read")));

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, request);

        // then
        assertThat(result.genres()).containsExactlyInAnyOrder("Sci-Fi", "Adventure");
        assertThat(result.tags()).containsExactlyInAnyOrder("classic", "must-read");
        assertThat(result.title()).isEqualTo("Dune"); // niezmieniony
    }

    @Test
    void shouldPatchIsbnDescriptionAndPageCount() {
        // given
        var existing = new Book();
        existing.setId(1L);
        existing.setTitle("Dune");
        existing.setIsbn("000-old");
        existing.setDescription("Stary opis");
        existing.setPageCount(100);

        var request = new BookPatchRequest();
        request.setIsbn("978-0441013593");
        request.setDescription("Nowy opis");
        request.setPageCount(412);

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, request);

        // then
        assertThat(result.isbn()).isEqualTo("978-0441013593");
        assertThat(result.description()).isEqualTo("Nowy opis");
        assertThat(result.pageCount()).isEqualTo(412);
        assertThat(result.title()).isEqualTo("Dune"); // niezmieniony
    }

    // ========== delete ==========

    @Test
    void shouldDeleteBookById() {
        // when
        bookService.delete(1L);

        // then
        verify(bookRepository).deleteById(1L);
    }

    private Author makeAuthor(String name) {
        Author author = new Author();
        author.setId(1L);
        author.setName(name);
        return author;
    }

    private BookAuthor makeBookAuthor(Book book, String name) {
        BookAuthor bookAuthor = new BookAuthor();
        bookAuthor.setBook(book);
        bookAuthor.setAuthor(makeAuthor(name));
        bookAuthor.setRole(AuthorRole.AUTHOR);
        return bookAuthor;
    }

    private Tag makeTag(String name) {
        Tag tag = new Tag();
        tag.setId(1L);
        tag.setName(name);
        return tag;
    }

    private BookTag makeBookTag(Book book, String name) {
        BookTag bookTag = new BookTag();
        bookTag.setBook(book);
        bookTag.setTag(makeTag(name));
        return bookTag;
    }

}
