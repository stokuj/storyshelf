package com.stokuj.books.service;

import com.stokuj.books.dto.bookshelf.UserBookRequest;
import com.stokuj.books.dto.bookshelf.UserBookResponse;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.domain.entity.Book;
import com.stokuj.books.domain.enums.ReadingStatus;
import com.stokuj.books.domain.entity.User;
import com.stokuj.books.domain.entity.UserBook;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.UserBookRepository;
import com.stokuj.books.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class UserBookService {

    private final UserBookRepository userBookRepository;
    private final UserRepository userRepository;
    private final BookRepository bookRepository;

    public UserBookService(UserBookRepository userBookRepository,
                           UserRepository userRepository,
                           BookRepository bookRepository) {
        this.userBookRepository = userBookRepository;
        this.userRepository = userRepository;
        this.bookRepository = bookRepository;
    }

    public List<UserBookResponse> getMyBooks(String email) {
        return userBookRepository.findAllByUserEmailOrderByCreatedAtDesc(email)
                .stream()
                .map(ub -> new UserBookResponse(ub.getBook(), ub.getStatus(), ub.getCreatedAt()))
                .toList();
    }

    public Optional<UserBookResponse> findByUserAndBook(String email, Long bookId) {
        return userBookRepository.findByUserEmailAndBookId(email, bookId)
                .map(ub -> new UserBookResponse(ub.getBook(), ub.getStatus(), ub.getCreatedAt()));
    }

    @Transactional
    public UserBookResponse addToShelf(String email, Long bookId, UserBookRequest request) {
        if (userBookRepository.findByUserEmailAndBookId(email, bookId).isPresent()) {
            throw new ConflictException("Ta ksiazka jest juz na polce");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

        ReadingStatus status = (request != null && request.getStatus() != null)
                ? request.getStatus()
                : ReadingStatus.WANT_TO_READ;

        UserBook userBook = new UserBook();
        userBook.setUser(user);
        userBook.setBook(book);
        userBook.setStatus(status);
        userBookRepository.save(userBook);

        return new UserBookResponse(book, userBook.getStatus(), userBook.getCreatedAt());
    }

    @Transactional
    public UserBookResponse updateStatus(String email, Long bookId, UserBookRequest request) {
        UserBook userBook = userBookRepository.findByUserEmailAndBookId(email, bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book is not on your shelf"));

        if (request == null || request.getStatus() == null) {
            throw new ResourceNotFoundException("Status is required");
        }

        userBook.setStatus(request.getStatus());
        userBookRepository.save(userBook);

        return new UserBookResponse(userBook.getBook(), userBook.getStatus(), userBook.getCreatedAt());
    }

    @Transactional
    public void removeFromShelf(String email, Long bookId) {
        UserBook userBook = userBookRepository.findByUserEmailAndBookId(email, bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book is not on your shelf"));
        userBookRepository.delete(userBook);
    }
}
