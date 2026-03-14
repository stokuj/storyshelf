package com.stokuj.books.model.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.stokuj.books.model.fastapi.FindPairsResult;
import com.stokuj.books.model.fastapi.NerResult;
import com.stokuj.books.model.fastapi.RelationsResult;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "book_chapters")
public class BookChapter {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_id", nullable = false)
    @JsonIgnore
    private Book book;

    @Column(nullable = false)
    private Integer chapterNumber;

    @Column(length = 500)
    private String title;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String content;

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// Analysis part - ENDPOINT FROM FAST API /analysis/
    private Boolean analysisCompleted = false;

    private Integer charCount;

    private Integer charCountClean;

    private Integer wordCount;

    private Integer tokenCount;
    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// NER part - ENDPOINT FROM FAST API /NER/{task_id}
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private NerResult nerResult;

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// find-pairs part - ENDPOINT FROM FAST API /find-pairs/
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private FindPairsResult findPairsResult;

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// relations part - ENDPOINT FROM FAST API /relations/
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private RelationsResult relationsResult;

}
