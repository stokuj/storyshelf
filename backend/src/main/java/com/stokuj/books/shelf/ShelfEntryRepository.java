package com.stokuj.books.shelf;

import com.stokuj.books.shelf.ShelfEntry;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ShelfEntryRepository extends JpaRepository<ShelfEntry, Long> {
    List<ShelfEntry> findAllByUserEmailOrderByCreatedAtDesc(String email);
    Optional<ShelfEntry> findByUserEmailAndBookId(String email, Long bookId);
}
