package com.stokuj.books.book.chapter;

import com.stokuj.books.book.chapter.Chapter;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookChapterRepository extends JpaRepository<Chapter, Long> {
    void deleteAllByBookId(Long bookId);
    int countByBookId(Long bookId);
    List<Chapter> findAllByBookIdOrderByChapterNumber(Long bookId);
}
