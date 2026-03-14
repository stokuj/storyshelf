package com.stokuj.books.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import com.stokuj.books.model.entity.BookChapter;

public interface BookChapterRepository extends JpaRepository<BookChapter, Long> {
    List<BookChapter> findAllByBookIdOrderByChapterNumber(Long bookId);
    void deleteAllByBookId(Long bookId);
}
