package com.stokuj.books.service;

import com.stokuj.books.domain.entity.*;
import com.stokuj.books.domain.enums.AuthorRole;
import com.stokuj.books.dto.book.BookPatchRequest;
import com.stokuj.books.dto.book.BookRequest;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.AuthorRepository;
import com.stokuj.books.repository.TagRepository;
import org.springframework.stereotype.Service;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

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

    public List<Book> getAll() {
        return bookRepository.findAll();
    }

    public List<Book> search(String query) {
        if (query == null || query.isBlank()) {
            return getAll();
        }
        String trimmed = query.trim();
        return bookRepository
                .searchByTitleAuthorOrGenre(
                        trimmed,
                        trimmed,
                        trimmed
                );
    }

    public Book getById(Long id) {
        return bookRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));
    }

    public Book create(BookRequest request) {
        Book book = new Book();
        mapRequestToBook(request, book);
        return bookRepository.save(book);
    }

    public Book update(Long id, BookRequest request) {
        Book existing = getById(id);
        mapRequestToBook(request, existing);
        return bookRepository.save(existing);
    }

    public Book patch(Long id, BookPatchRequest request) {
        Book existing = getById(id);

        if (request.getTitle() != null) {
            existing.setTitle(request.getTitle());
        }
        if (request.getAuthor() != null) {
            updateAuthors(existing, request.getAuthor());
        }
        if (request.getYear() != null) {
            existing.setYear(request.getYear());
        }
        if (request.getIsbn() != null) {
            existing.setIsbn(request.getIsbn());
        }
        if (request.getDescription() != null) {
            existing.setDescription(request.getDescription());
        }
        if (request.getPageCount() != null) {
            existing.setPageCount(request.getPageCount());
        }
        if (request.getGenres() != null) {
            existing.setGenres(request.getGenres());
        }
        if (request.getTags() != null) {
            updateTags(existing, request.getTags());
        }

        return bookRepository.save(existing);
    }

    public void delete(Long id) {
        bookRepository.deleteById(id);
    }

    private void mapRequestToBook(BookRequest request, Book book) {
        book.setTitle(request.getTitle());
        book.setYear(request.getYear());
        book.setIsbn(request.getIsbn());
        book.setDescription(request.getDescription());
        book.setPageCount(request.getPageCount());
        book.setGenres(request.getGenres());
        updateAuthors(book, request.getAuthor());
        updateTags(book, request.getTags());
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
