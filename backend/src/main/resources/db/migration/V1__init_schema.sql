CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    role TEXT NOT NULL DEFAULT 'USER'
);

CREATE TABLE books (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    author TEXT,
    year INTEGER NOT NULL DEFAULT 0,
    isbn TEXT,
    description TEXT,
    page_count INTEGER NOT NULL DEFAULT 0,
    chapters_count INTEGER NOT NULL DEFAULT 0,
    ner_completed_count INTEGER NOT NULL DEFAULT 0,
    rating DOUBLE PRECISION NOT NULL DEFAULT 0,
    ratings_count INTEGER NOT NULL DEFAULT 0,
    version BIGINT NOT NULL DEFAULT 0,
    created_at DATE,
    updated_at DATE
);

CREATE TABLE characters (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE book_characters (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL,
    character_id BIGINT NOT NULL,
    mention_count INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_book_characters_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_book_characters_character
        FOREIGN KEY (character_id) REFERENCES characters(id)
        ON DELETE CASCADE,
    CONSTRAINT uk_book_character UNIQUE (book_id, character_id)
);

CREATE TABLE character_relations (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL,
    source_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    relation TEXT,
    evidence TEXT,
    confidence DOUBLE PRECISION,
    CONSTRAINT fk_character_relations_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_character_relations_source
        FOREIGN KEY (source_id) REFERENCES characters(id),
    CONSTRAINT fk_character_relations_target
        FOREIGN KEY (target_id) REFERENCES characters(id),
    CONSTRAINT uk_character_relation UNIQUE (book_id, source_id, target_id)
);

CREATE TABLE book_genres (
    book_id BIGINT NOT NULL,
    genre TEXT NOT NULL,
    CONSTRAINT fk_book_genres_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);

CREATE TABLE book_tags (
    book_id BIGINT NOT NULL,
    tag TEXT NOT NULL,
    CONSTRAINT fk_book_tags_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);

CREATE TABLE book_chapters (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL,
    chapter_number INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    analysis_completed BOOLEAN NOT NULL DEFAULT FALSE,
    char_count INTEGER,
    char_count_clean INTEGER,
    word_count INTEGER,
    token_count INTEGER,
    ner_result JSONB,
    CONSTRAINT fk_book_chapters_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);

CREATE TABLE user_books (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'WANT_TO_READ',
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uk_user_book UNIQUE (user_id, book_id),
    CONSTRAINT fk_user_books_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_books_book
        FOREIGN KEY (book_id) REFERENCES books(id)
        ON DELETE CASCADE
);