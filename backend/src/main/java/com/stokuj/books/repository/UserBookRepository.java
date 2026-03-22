package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Bookshelf;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserBookRepository extends JpaRepository<Bookshelf, Long> {
    List<Bookshelf> findAllByUserEmailOrderByCreatedAtDesc(String email);

    Optional<Bookshelf> findByUserEmailAndBookId(String email, Long bookId);
}
