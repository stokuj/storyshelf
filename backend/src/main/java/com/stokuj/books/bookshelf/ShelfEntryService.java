package com.stokuj.books.bookshelf;

import com.stokuj.books.book.book.Book;
import com.stokuj.books.bookshelf.dto.ShelfEntryRequest;
import com.stokuj.books.bookshelf.dto.ShelfEntryResponse;
import com.stokuj.books.user.User;
import com.stokuj.books.exception.ConflictException;
import com.stokuj.books.exception.ResourceNotFoundException;
import com.stokuj.books.book.book.BookRepository;
import com.stokuj.books.user.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
public class ShelfEntryService {

    private final ShelfEntryRepository shelfEntryRepository;
    private final UserRepository userRepository;
    private final BookRepository bookRepository;

    public ShelfEntryService(ShelfEntryRepository shelfEntryRepository,
                             UserRepository userRepository,
                             BookRepository bookRepository) {
        this.shelfEntryRepository = shelfEntryRepository;
        this.userRepository = userRepository;
        this.bookRepository = bookRepository;
    }

    public List<ShelfEntryResponse> getMyBooks(String email) {
        return shelfEntryRepository.findAllByUserEmailOrderByCreatedAtDesc(email)
                .stream()
                .map(ub -> new ShelfEntryResponse(
                        new ShelfEntryResponse.BookSummary(ub.getBook().getId(), ub.getBook().getTitle(), ub.getBook().getAuthor()), 
                        ub.getStatus(), 
                        ub.getCreatedAt()))
                .toList();
    }

    public Optional<ShelfEntryResponse> findByUserAndBook(String email, Long bookId) {
        return shelfEntryRepository.findByUserEmailAndBookId(email, bookId)
                .map(ub -> new ShelfEntryResponse(
                        new ShelfEntryResponse.BookSummary(ub.getBook().getId(), ub.getBook().getTitle(), ub.getBook().getAuthor()), 
                        ub.getStatus(), 
                        ub.getCreatedAt()));
    }

    @Transactional
    public ShelfEntryResponse addToShelf(String email, Long bookId, ShelfEntryRequest request) {
        if (shelfEntryRepository.findByUserEmailAndBookId(email, bookId).isPresent()) {
            throw new ConflictException("Ta ksiazka jest juz na polce");
        }

        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Book book = bookRepository.findById(bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book not found"));

        ReadingStatus status = (request != null && request.getStatus() != null)
                ? request.getStatus()
                : ReadingStatus.WANT_TO_READ;

        ShelfEntry shelfEntry = new ShelfEntry();
        shelfEntry.setUser(user);
        shelfEntry.setBook(book);
        shelfEntry.setStatus(status);
        shelfEntryRepository.save(shelfEntry);

        return new ShelfEntryResponse(
                new ShelfEntryResponse.BookSummary(book.getId(), book.getTitle(), book.getAuthor()), 
                shelfEntry.getStatus(), 
                shelfEntry.getCreatedAt());
    }

    @Transactional
    public ShelfEntryResponse updateStatus(String email, Long bookId, ShelfEntryRequest request) {
        ShelfEntry shelfEntry = shelfEntryRepository.findByUserEmailAndBookId(email, bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book is not on your shelf"));

        if (request == null || request.getStatus() == null) {
            throw new ResourceNotFoundException("Status is required");
        }

        shelfEntry.setStatus(request.getStatus());
        shelfEntryRepository.save(shelfEntry);

        return new ShelfEntryResponse(
                new ShelfEntryResponse.BookSummary(shelfEntry.getBook().getId(), shelfEntry.getBook().getTitle(), shelfEntry.getBook().getAuthor()), 
                shelfEntry.getStatus(), 
                shelfEntry.getCreatedAt());
    }

    @Transactional
    public void removeFromShelf(String email, Long bookId) {
        ShelfEntry shelfEntry = shelfEntryRepository.findByUserEmailAndBookId(email, bookId)
                .orElseThrow(() -> new ResourceNotFoundException("Book is not on your shelf"));
        shelfEntryRepository.delete(shelfEntry);
    }
}
