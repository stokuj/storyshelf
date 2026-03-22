package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Book;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface BookRepository extends JpaRepository<Book, Long> {
    @Query("SELECT b FROM Book b JOIN b.bookAuthors ba JOIN ba.author a JOIN b.genres g WHERE lower(b.title) LIKE lower(concat('%',:title,'%')) OR lower(a.name) LIKE lower(concat('%',:author,'%')) OR lower(g) LIKE lower(concat('%',:genre,'%'))")
    List<Book> searchByTitleAuthorOrGenre(String title, String author, String genre);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT b FROM Book b WHERE b.id = :id")
    Optional<Book> findByIdForUpdate(Long id);

}
