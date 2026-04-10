package com.stokuj.books.shelf;

import com.stokuj.books.shelf.UserBook;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserBookRepository extends JpaRepository<UserBook, Long> {
    List<UserBook> findAllByUserEmailOrderByCreatedAtDesc(String email);
    Optional<UserBook> findByUserEmailAndBookId(String email, Long bookId);
}
