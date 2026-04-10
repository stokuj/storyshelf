package com.stokuj.books.series;

import com.stokuj.books.series.Series;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SeriesRepository extends JpaRepository<Series, Long> {
}
