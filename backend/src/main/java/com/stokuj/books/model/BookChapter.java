package com.stokuj.books.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
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
}
