package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Chapter;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookChapterRepository extends JpaRepository<Chapter, Long> {
}
