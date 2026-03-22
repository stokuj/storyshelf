package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Book;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import jakarta.persistence.LockModeType;

import java.util.List;
import java.util.Optional;

public interface BookRepository extends JpaRepository<Book, Long> {
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT b FROM Book b WHERE b.id = :id")
    Optional<Book> findByIdForUpdate(@Param("id") Long id);

    @Query("""
            SELECT DISTINCT b
            FROM Book b
            LEFT JOIN b.bookAuthors ba
            LEFT JOIN ba.author a
            LEFT JOIN b.genres g
            WHERE LOWER(b.title) LIKE LOWER(CONCAT('%', :title, '%'))
               OR LOWER(a.name) LIKE LOWER(CONCAT('%', :author, '%'))
               OR LOWER(g) LIKE LOWER(CONCAT('%', :genre, '%'))
            """)
    List<Book> searchByTitleAuthorOrGenre(
            @Param("title") String title,
            @Param("author") String author,
            @Param("genre") String genre
    );
}
