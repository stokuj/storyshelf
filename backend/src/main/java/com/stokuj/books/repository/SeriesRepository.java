package com.stokuj.books.repository;

import com.stokuj.books.domain.entity.Series;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SeriesRepository extends JpaRepository<Series, Long> {
}
