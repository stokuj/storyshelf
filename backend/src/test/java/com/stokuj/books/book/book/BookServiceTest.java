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
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
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

    @Nested
    class Querying {

        @Test
        void shouldReturnAllBooks() {
            Book dune = book(1L, "Dune", 1965);
            Book foundation = book(2L, "Foundation", 1951);
            given(bookRepository.findAll()).willReturn(List.of(dune, foundation));

            List<BookResponse> result = bookService.getAll();

            assertThat(result).hasSize(2);
            assertThat(result.get(0).title()).isEqualTo("Dune");
            assertThat(result.get(1).title()).isEqualTo("Foundation");
        }

        @Test
        void shouldSearchAllWhenQueryIsBlank() {
            given(bookRepository.findAll()).willReturn(List.of(book(1L, "Dune", 1965)));

            List<BookResponse> result = bookService.search("   ");

            assertThat(result).hasSize(1);
            verify(bookRepository).findAll();
        }

        @Test
        void shouldSearchByTrimmedQuery() {
            Book dune = book(1L, "Dune", 1965);
            given(bookRepository.searchByTitleAuthorOrGenre("Dune", "Dune", "Dune")).willReturn(List.of(dune));

            List<BookResponse> result = bookService.search("  Dune  ");

            assertThat(result).hasSize(1);
            assertThat(result.getFirst().title()).isEqualTo("Dune");
            verify(bookRepository).searchByTitleAuthorOrGenre("Dune", "Dune", "Dune");
        }

        @Test
        void shouldGetBookById() {
            Book dune = book(1L, "Dune", 1965);
            given(bookRepository.findById(1L)).willReturn(Optional.of(dune));

            BookResponse result = bookService.getById(1L);

            assertThat(result.id()).isEqualTo(1L);
            assertThat(result.title()).isEqualTo("Dune");
        }

        @Test
        void shouldThrowWhenBookNotFound() {
            given(bookRepository.findById(999L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> bookService.getById(999L))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Book not found");
        }
    }

    @Nested
    class CreateAndUpdate {

        @Test
        void shouldCreateBookWithAuthorAndTags() {
            BookRequest request = new BookRequest(
                    "Dune",
                    10L,
                    1965,
                    "isbn",
                    "desc",
                    412,
                    Set.of("Sci-Fi"),
                    Set.of("classic", "space")
            );
            Author author = author(10L, "Frank Herbert");
            Tag t1 = tag(100L, "classic");
            Tag t2 = tag(101L, "space");
            given(authorRepository.findById(10L)).willReturn(Optional.of(author));
            given(tagRepository.findByNameIgnoreCase("classic")).willReturn(Optional.of(t1));
            given(tagRepository.findByNameIgnoreCase("space")).willReturn(Optional.of(t2));
            given(bookRepository.save(any(Book.class)))
                    .willAnswer(invocation -> invocation.getArgument(0));

            BookResponse result = bookService.create(request);

            ArgumentCaptor<Book> captor = ArgumentCaptor.forClass(Book.class);
            verify(bookRepository).save(captor.capture());
            Book saved = captor.getValue();
            assertThat(getField(saved, "title")).isEqualTo("Dune");
            assertThat(getField(saved, "year")).isEqualTo(1965);
            assertThat(getField(saved, "pageCount")).isEqualTo(412);
            assertThat((List<?>) getField(saved, "bookAuthors")).hasSize(1);
            assertThat((List<?>) getField(saved, "bookTags")).hasSize(2);
            assertThat(result.title()).isEqualTo("Dune");
        }

        @Test
        void shouldThrowWhenAuthorMissingOnCreate() {
            BookRequest request = new BookRequest("Dune", 10L, 1965, null, null, 412, Set.of(), Set.of());
            given(authorRepository.findById(10L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> bookService.create(request))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Author not found");
        }

        @Test
        void shouldCreateMissingTagsOnCreate() {
            BookRequest request = new BookRequest("Dune", 10L, 1965, null, null, 412, Set.of(), Set.of("new-tag"));
            Tag newTag = tag(777L, "new-tag");
            given(authorRepository.findById(10L)).willReturn(Optional.of(author(10L, "Frank Herbert")));
            given(tagRepository.findByNameIgnoreCase("new-tag")).willReturn(Optional.empty());
            given(tagRepository.save(any(Tag.class))).willReturn(newTag);
            given(bookRepository.save(any(Book.class))).willAnswer(invocation -> invocation.getArgument(0));

            BookResponse result = bookService.create(request);

            ArgumentCaptor<Tag> tagCaptor = ArgumentCaptor.forClass(Tag.class);
            verify(tagRepository).save(tagCaptor.capture());
            assertThat(getField(tagCaptor.getValue(), "name")).isEqualTo("new-tag");
            assertThat(result.tags()).containsExactly("new-tag");
        }

        @Test
        void shouldUpdateBook() {
            Book existing = book(1L, "Old", 1900);
            BookRequest request = new BookRequest("New", 10L, 1965, null, null, 300, Set.of("Drama"), Set.of());
            given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
            given(authorRepository.findById(10L)).willReturn(Optional.of(author(10L, "Frank Herbert")));
            given(bookRepository.save(existing)).willReturn(existing);

            BookResponse result = bookService.update(1L, request);

            assertThat(result.title()).isEqualTo("New");
            assertThat(getField(existing, "year")).isEqualTo(1965);
            assertThat((Set<String>) getField(existing, "genres")).contains("Drama");
        }
    }

    @Nested
    class Patch {

        @Test
        void shouldPatchOnlyProvidedFields() {
            Book existing = book(1L, "Dune", 1965);
            setField(existing, "pageCount", 412);
            setField(existing, "description", "old");
            BookPatchRequest patch = new BookPatchRequest("Dune Messiah", null, null, null, null, null, null, null);
            given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
            given(bookRepository.save(existing)).willReturn(existing);

            BookResponse result = bookService.patch(1L, patch);

            assertThat(result.title()).isEqualTo("Dune Messiah");
            assertThat(getField(existing, "year")).isEqualTo(1965);
            assertThat(getField(existing, "pageCount")).isEqualTo(412);
            assertThat(getField(existing, "description")).isEqualTo("old");
        }

        @Test
        void shouldPatchAuthorAndTagsWhenProvided() {
            Book existing = book(1L, "Dune", 1965);
            BookPatchRequest patch = new BookPatchRequest(null, 10L, null, null, null, null, null, Set.of("classic"));
            given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
            given(authorRepository.findById(10L)).willReturn(Optional.of(author(10L, "Frank Herbert")));
            given(tagRepository.findByNameIgnoreCase("classic")).willReturn(Optional.of(tag(100L, "classic")));
            given(bookRepository.save(existing)).willReturn(existing);

            bookService.patch(1L, patch);

            assertThat((List<?>) getField(existing, "bookAuthors")).hasSize(1);
            assertThat((List<?>) getField(existing, "bookTags")).hasSize(1);
        }

        @Test
        void shouldThrowWhenAuthorMissingOnPatch() {
            Book existing = book(1L, "Dune", 1965);
            BookPatchRequest patch = new BookPatchRequest(null, 10L, null, null, null, null, null, null);
            given(bookRepository.findById(1L)).willReturn(Optional.of(existing));
            given(authorRepository.findById(10L)).willReturn(Optional.empty());

            assertThatThrownBy(() -> bookService.patch(1L, patch))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessage("Author not found");
        }
    }

    @Test
    void shouldDeleteById() {
        bookService.delete(5L);

        verify(bookRepository).deleteById(5L);
    }

    private Book book(Long id, String title, int year) {
        Book book = new Book();
        setField(book, "id", id);
        setField(book, "title", title);
        setField(book, "year", year);
        setField(book, "bookAuthors", new ArrayList<>());
        setField(book, "bookTags", new ArrayList<>());
        setField(book, "genres", new java.util.HashSet<>());
        return book;
    }

    private Author author(Long id, String name) {
        Author author = new Author();
        setField(author, "id", id);
        setField(author, "name", name);
        return author;
    }

    private Tag tag(Long id, String name) {
        Tag tag = new Tag();
        setField(tag, "id", id);
        setField(tag, "name", name);
        return tag;
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

    private Object getField(Object target, String fieldName) {
        try {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            return field.get(target);
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
