package com.stokuj.books.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import com.stokuj.books.domain.entity.Chapter;

public interface BookChapterRepository extends JpaRepository<Chapter, Long> {
    List<Chapter> findAllByBookIdOrderByChapterNumber(Long bookId);
    void deleteAllByBookId(Long bookId);
    int countByBookId(Long bookId);
}
