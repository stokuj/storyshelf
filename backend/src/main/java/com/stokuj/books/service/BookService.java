package com.stokuj.books.service;

import com.stokuj.books.dto.BookPatchRequest;
import com.stokuj.books.dto.BookRequest;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.repository.BookRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class BookService {

    private final BookRepository bookRepository;

    public BookService(BookRepository bookRepository) {
        this.bookRepository = bookRepository;
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
                .findByTitleContainingIgnoreCaseOrAuthorContainingIgnoreCaseOrGenresContainingIgnoreCase(
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
            existing.setAuthor(request.getAuthor());
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
            existing.setTags(request.getTags());
        }

        return bookRepository.save(existing);
    }

    public void delete(Long id) {
        bookRepository.deleteById(id);
    }

    private void mapRequestToBook(BookRequest request, Book book) {
        book.setTitle(request.getTitle());
        book.setAuthor(request.getAuthor());
        book.setYear(request.getYear());
        book.setIsbn(request.getIsbn());
        book.setDescription(request.getDescription());
        book.setPageCount(request.getPageCount());
        book.setGenres(request.getGenres());
        book.setTags(request.getTags());
    }

}
