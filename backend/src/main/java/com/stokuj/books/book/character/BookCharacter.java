package com.stokuj.books.book.character;

import com.stokuj.books.book.book.Book;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Entity
@Table(name = "book_characters",
        uniqueConstraints = @UniqueConstraint(
                name = "uk_book_character",
                columnNames = {"book_id", "character_id"}))
public class BookCharacter {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "book_id", nullable = false)
    private Book book;

    @ManyToOne(fetch = FetchType.EAGER, optional = false)
    @JoinColumn(name = "character_id", nullable = false)
    private StoryCharacter character;

    @Column(name = "mention_count", nullable = false)
    private int mentionCount;

    @Column(name = "role")
    private String role;
}
