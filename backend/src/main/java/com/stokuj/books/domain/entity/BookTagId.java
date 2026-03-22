package com.stokuj.books.domain.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class BookTagId implements Serializable {

    @Column(name = "book_id")
    private Long bookId;

    @Column(name = "tag_id")
    private Long tagId;

    public BookTagId() {
    }

    public BookTagId(Long bookId, Long tagId) {
        this.bookId = bookId;
        this.tagId = tagId;
    }

    public Long getBookId() {
        return bookId;
    }

    public Long getTagId() {
        return tagId;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        BookTagId that = (BookTagId) o;
        return Objects.equals(bookId, that.bookId) && Objects.equals(tagId, that.tagId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(bookId, tagId);
    }
}
