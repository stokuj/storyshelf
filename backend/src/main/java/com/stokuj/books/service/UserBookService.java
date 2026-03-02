package com.stokuj.books.service;

import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.model.Book;
import com.stokuj.books.model.User;
import com.stokuj.books.model.UserBook;
import com.stokuj.books.repository.BookRepository;
import com.stokuj.books.repository.UserBookRepository;
import com.stokuj.books.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

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

    public List<Book> getMyReadBooks(String email) {
        return userBookRepository.findAllByUserEmailOrderByCreatedAtDesc(email)
                .stream()
                .map(UserBook::getBook)
                .toList();
    }

    @Transactional
    public Book markAsRead(String email, Long bookId) {
        if (userBookRepository.findByUserEmailAndBookId(email, bookId).isPresent()) {
            throw new ConflictException("Ta ksiazka jest juz na liscie przeczytanych");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

        UserBook userBook = new UserBook();
        userBook.setUser(user);
        userBook.setBook(book);
        userBookRepository.save(userBook);

        return book;
    }

    @Transactional
    public void unmarkAsRead(String email, Long bookId) {
        UserBook userBook = userBookRepository.findByUserEmailAndBookId(email, bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book is not on your read list"));
        userBookRepository.delete(userBook);
    }
}
