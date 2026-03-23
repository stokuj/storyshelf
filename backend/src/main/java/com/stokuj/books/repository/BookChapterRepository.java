package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Chapter;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface BookChapterRepository extends JpaRepository<Chapter, Long> {
    void deleteAllByBookId(Long bookId);
    int countByBookId(Long bookId);
    List<Chapter> findAllByBookIdOrderByChapterNumber(Long bookId);
}
