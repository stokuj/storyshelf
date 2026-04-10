package com.stokuj.books.book.chapter;

import com.stokuj.books.book.book.Book;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.stokuj.books.analysis.NerResult;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "book_chapters")
public class Chapter {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_id", nullable = false)
    @JsonIgnore
    private Book book;

    @Column(name = "chapter_number", nullable = false)
    private Integer chapterNumber;

    @Column(length = 500)
    private String title;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    @Column(name = "analysis_completed")
    private Boolean analysisCompleted = false;

    @Column(name = "char_count")
    private Integer charCount;

    @Column(name = "char_count_clean")
    private Integer charCountClean;

    @Column(name = "word_count")
    private Integer wordCount;

    @Column(name = "token_count")
    private Integer tokenCount;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "ner_result", columnDefinition = "jsonb")
    private NerResult nerResult;
}
