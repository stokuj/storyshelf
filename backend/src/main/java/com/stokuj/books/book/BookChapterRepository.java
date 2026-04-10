package com.stokuj.books.book;

import com.stokuj.books.book.Chapter;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookChapterRepository extends JpaRepository<Chapter, Long> {
    void deleteAllByBookId(Long bookId);
    int countByBookId(Long bookId);
    List<Chapter> findAllByBookIdOrderByChapterNumber(Long bookId);
}
