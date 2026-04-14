package com.stokuj.books.book.book;

import com.stokuj.books.author.Author;
import com.stokuj.books.author.AuthorRepository;
import com.stokuj.books.book.book.dto.BookPatchRequest;
import com.stokuj.books.book.book.dto.BookRequest;
import com.stokuj.books.book.book.dto.BookResponse;
import com.stokuj.books.book.tag.BookTag;
import com.stokuj.books.book.tag.Tag;
import com.stokuj.books.book.tag.TagRepository;
import com.stokuj.books.exception.ResourceNotFoundException;
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

    @Mock BookRepository bookRepository;
    @Mock AuthorRepository authorRepository;
    @Mock TagRepository tagRepository;

    @InjectMocks BookService bookService;

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
        var request = new BookRequest(
                "Dune",
                "Herbert",
                1965,
                "978-0441013593",
                null,
                0,
                Set.of("Sci-Fi"),
                null
        );

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

        var request = new BookRequest(
                "Dune",
                "Herbert",
                1965,
                null,
                null,
                0,
                null,
                null
        );

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
        assertThatThrownBy(() -> bookService.update(99L, new BookRequest(
                "Dune",
                "Herbert",
                1965,
                null,
                null,
                0,
                null,
                null
        )))
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

        var patchRequest = new BookPatchRequest(
                "New Title",
                null,
                null,
                null,
                null,
                null,
                null,
                null
        );
        // author = null -> should not be overwritten

        given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
        given(bookRepository.save(any(Book.class))).willAnswer(inv -> inv.getArgument(0));

        // when
        var result = bookService.patch(1L, patchRequest);

        // then
        assertThat(result.title()).isEqualTo("New Title");
        assertThat(result.author()).isEqualTo("Old Author"); // unchanged!
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
        var result = bookService.patch(1L, new BookPatchRequest(null, null, null, null, null, null, null, null)); // all fields null

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

        var request = new BookPatchRequest(
                "New Title",
                "New Author",
                2024,
                null,
                null,
                null,
                null,
                null
        );

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
        assertThatThrownBy(() -> bookService.patch(99L, new BookPatchRequest(null, null, null, null, null, null, null, null)))
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

        var request = new BookPatchRequest(
                null,
                null,
                null,
                null,
                null,
                null,
                Set.of("Sci-Fi", "Adventure"),
                List.of("classic", "must-read")
        );

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

        var request = new BookPatchRequest(
                null,
                null,
                null,
                "978-0441013593",
                "Nowy opis",
                412,
                null,
                null
        );

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
