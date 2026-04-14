package com.stokuj.books.book.book;

import com.stokuj.books.author.Author;
import com.stokuj.books.book.book.dto.BookPatchRequest;
import com.stokuj.books.book.book.dto.BookRequest;
import com.stokuj.books.book.book.dto.BookResponse;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.author.AuthorRepository;
import org.springframework.stereotype.Service;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import com.stokuj.books.book.tag.Tag;
import com.stokuj.books.book.tag.TagRepository;
import com.stokuj.books.book.tag.BookTag;
@Service
public class BookService {

    private final BookRepository bookRepository;
    private final AuthorRepository authorRepository;
    private final TagRepository tagRepository;

    public BookService(BookRepository bookRepository,
                       AuthorRepository authorRepository,
                       TagRepository tagRepository) {
        this.bookRepository = bookRepository;
        this.authorRepository = authorRepository;
        this.tagRepository = tagRepository;
    }

    public BookResponse toDto(Book book) {
        return new BookResponse(
                book.getId(),
                book.getTitle(),
                book.getAuthor(),
                book.getYear(),
                book.getIsbn(),
                book.getDescription(),
                book.getPageCount(),
                book.getGenres(),
                book.getTags(),
                book.getRating(),
                book.getRatingsCount()
        );
    }

    public List<BookResponse> getAll() {
        return bookRepository.findAll().stream().map(this::toDto).toList();
    }

    public List<BookResponse> search(String query) {
        if (query == null || query.isBlank()) {
            return getAll();
        }
        String trimmed = query.trim();
        return bookRepository
                .searchByTitleAuthorOrGenre(
                        trimmed,
                        trimmed,
                        trimmed
                ).stream().map(this::toDto).toList();
    }

    public Book getEntityById(Long id) {
        return bookRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));
    }

    public BookResponse getById(Long id) {
        return toDto(getEntityById(id));
    }

    public BookResponse create(BookRequest request) {
        Book book = new Book();
        mapRequestToBook(request, book);
        return toDto(bookRepository.save(book));
    }

    public BookResponse update(Long id, BookRequest request) {
        Book existing = getEntityById(id);
        mapRequestToBook(request, existing);
        return toDto(bookRepository.save(existing));
    }

    public BookResponse patch(Long id, BookPatchRequest request) {
        Book existing = getEntityById(id);

        if (request.title() != null) {
            existing.setTitle(request.title());
        }
        if (request.author() != null) {
            updateAuthors(existing, request.author());
        }
        if (request.year() != null) {
            existing.setYear(request.year());
        }
        if (request.isbn() != null) {
            existing.setIsbn(request.isbn());
        }
        if (request.description() != null) {
            existing.setDescription(request.description());
        }
        if (request.pageCount() != null) {
            existing.setPageCount(request.pageCount());
        }
        if (request.genres() != null) {
            existing.setGenres(request.genres());
        }
        if (request.tags() != null) {
            updateTags(existing, request.tags());
        }

        return toDto(bookRepository.save(existing));
    }

    public void delete(Long id) {
        bookRepository.deleteById(id);
    }

    private void mapRequestToBook(BookRequest request, Book book) {
        book.setTitle(request.title());
        book.setYear(request.year());
        book.setIsbn(request.isbn());
        book.setDescription(request.description());
        book.setPageCount(request.pageCount());
        book.setGenres(request.genres());
        updateAuthors(book, request.author());
        updateTags(book, request.tags());
    }

    private void updateAuthors(Book book, String authorName) {
        book.getBookAuthors().clear();
        if (authorName == null || authorName.isBlank()) {
            return;
        }
        String normalized = authorName.trim();
        Author author = authorRepository.findByNameIgnoreCase(normalized)
                .orElseGet(() -> {
                    Author created = new Author();
                    created.setName(normalized);
                    return authorRepository.save(created);
                });
        BookAuthor bookAuthor = new BookAuthor();
        bookAuthor.setBook(book);
        bookAuthor.setAuthor(author);
        bookAuthor.setRole(AuthorRole.AUTHOR);
        book.getBookAuthors().add(bookAuthor);
    }

    private void updateTags(Book book, List<String> tags) {
        book.getBookTags().clear();
        if (tags == null) {
            return;
        }
        Set<String> normalizedTags = new LinkedHashSet<>();
        for (String tagName : tags) {
            if (tagName == null) {
                continue;
            }
            String trimmed = tagName.trim();
            if (trimmed.isEmpty()) {
                continue;
            }
            normalizedTags.add(trimmed);
        }
        for (String name : normalizedTags) {
            Tag tag = tagRepository.findByNameIgnoreCase(name)
                    .orElseGet(() -> {
                        Tag created = new Tag();
                        created.setName(name);
                        return tagRepository.save(created);
                    });
            BookTag bookTag = new BookTag();
            bookTag.setBook(book);
            bookTag.setTag(tag);
            book.getBookTags().add(bookTag);
        }
    }

}
