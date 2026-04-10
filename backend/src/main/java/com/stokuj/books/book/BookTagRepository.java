package com.stokuj.books.book;

import com.stokuj.books.book.BookTag;
import org.springframework.data.jpa.repository.JpaRepository;

public interface BookTagRepository extends JpaRepository<BookTag, Long> {
}
