package com.stokuj.books.book.book;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.stokuj.books.series.Series;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.stokuj.books.book.chapter.Chapter;
import com.stokuj.books.book.tag.BookTag;
@Getter
@Setter
@Entity
@Table(name = "books")
public class Book {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Version
    private Long version;

    private String title;
    private int year;
    private String isbn;
    private String description;

    @Column(name = "page_count")
    private int pageCount;

    @ElementCollection
    @CollectionTable(name = "book_genres", joinColumns = @JoinColumn(name = "book_id"))
    @Column(name = "genre")
    private Set<String> genres = new HashSet<>();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "series_id")
    private Series series;

    @Column(name = "position_in_series")
    private Integer positionInSeries;

    @OneToMany(mappedBy = "book", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<BookAuthor> bookAuthors = new ArrayList<>();

    @OneToMany(mappedBy = "book", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<BookTag> bookTags = new ArrayList<>();

    @OneToMany(mappedBy = "book", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("chapterNumber ASC")
    @JsonIgnore
    private List<Chapter> chapters = new ArrayList<>();

    @Column(name = "chapters_count")
    private int chaptersCount;

    @Column(name = "ner_completed_count")
    private int nerCompletedCount;

    private double rating;

    @Column(name = "ratings_count")
    private int ratingsCount;

    @Column(name = "created_at")
    private LocalDate createdAt;

    @Column(name = "updated_at")
    private LocalDate updatedAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDate.now();
        this.updatedAt = LocalDate.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDate.now();
    }

    public String getAuthor() {
        if (bookAuthors == null || bookAuthors.isEmpty()) return null;
        return bookAuthors.stream()
                .map(ba -> ba.getAuthor() != null ? ba.getAuthor().getName() : null)
                .filter(name -> name != null && !name.isBlank())
                .findFirst()
                .orElse(null);
    }

    public List<String> getTags() {
        if (bookTags == null) return List.of();
        return bookTags.stream()
                .map(bt -> bt.getTag() != null ? bt.getTag().getName() : null)
                .filter(name -> name != null && !name.isBlank())
                .toList();
    }
}
