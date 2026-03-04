package com.stokuj.books.service;

import com.stokuj.books.dto.BookRequest;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.Book;
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