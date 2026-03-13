package com.stokuj.books.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.stokuj.books.converter.FindPairsResultConverter;
import com.stokuj.books.converter.NerResultConverter;
import com.stokuj.books.converter.RelationsResultConverter;
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
    @Convert(converter = NerResultConverter.class)
    @Column(columnDefinition = "jsonb")
    private NerResult nerResult;

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// find-pairs part - ENDPOINT FROM FAST API /find-pairs/
    @Convert(converter = FindPairsResultConverter.class)
    @Column(columnDefinition = "jsonb")
    private FindPairsResult findPairsResult;

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///

    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
    /// relations part - ENDPOINT FROM FAST API /relations/
    @Convert(converter = RelationsResultConverter.class)
    @Column(columnDefinition = "jsonb")
    private RelationsResult relationsResult;
    /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// /// ///
}
