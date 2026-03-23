CREATE TABLE users (
                       id          BIGSERIAL PRIMARY KEY,
                       email       TEXT        NOT NULL UNIQUE,
                       password    TEXT,
                       role        TEXT        NOT NULL DEFAULT 'USER',
                       username    TEXT        NOT NULL UNIQUE,
                       bio         TEXT,
                       avatar_url  TEXT,
                       profile_public  BOOLEAN NOT NULL DEFAULT TRUE,
                       enabled     BOOLEAN     NOT NULL DEFAULT TRUE,
                       created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                       CONSTRAINT chk_users_role CHECK (role IN ('USER', 'MODERATOR', 'ADMIN'))
);

CREATE TABLE user_follows (
                              id           BIGSERIAL PRIMARY KEY,
                              follower_id  BIGINT NOT NULL,
                              following_id BIGINT NOT NULL,
                              followed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                              CONSTRAINT fk_follows_follower  FOREIGN KEY (follower_id)  REFERENCES users(id) ON DELETE CASCADE,
                              CONSTRAINT fk_follows_following FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
                              CONSTRAINT uk_user_follow UNIQUE (follower_id, following_id)
);

CREATE TABLE series (
                        id          BIGSERIAL PRIMARY KEY,
                        name        TEXT NOT NULL,
                        description TEXT,
                        cover_url   TEXT,
                        status      TEXT,
                        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE authors (
                         id         BIGSERIAL PRIMARY KEY,
                         name       TEXT NOT NULL,
                         bio        TEXT,
                         avatar_url TEXT,
                         birth_date DATE
);

CREATE TABLE books (
                       id                  BIGSERIAL PRIMARY KEY,
                       version             BIGINT  NOT NULL DEFAULT 0,
                       title               TEXT,
                       year                INTEGER NOT NULL DEFAULT 0,
                       isbn                TEXT,
                       description         TEXT,
                       page_count          INTEGER NOT NULL DEFAULT 0,
                       series_id           BIGINT,
                       position_in_series  INTEGER,
                       chapters_count      INTEGER NOT NULL DEFAULT 0,
                       ner_completed_count INTEGER NOT NULL DEFAULT 0,
                       rating              DOUBLE PRECISION NOT NULL DEFAULT 0,
                       ratings_count       INTEGER NOT NULL DEFAULT 0,
                       created_at          DATE,
                       updated_at          DATE,
                       CONSTRAINT fk_books_series FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL
);

CREATE TABLE book_authors (
                              id         BIGSERIAL PRIMARY KEY,
                              book_id    BIGINT NOT NULL,
                              author_id  BIGINT NOT NULL,
                              role       TEXT,
                              CONSTRAINT fk_book_authors_book   FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE CASCADE,
                              CONSTRAINT fk_book_authors_author FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
                              CONSTRAINT uk_book_author UNIQUE (book_id, author_id)
);

CREATE TABLE book_genres (
                             book_id BIGINT NOT NULL,
                             genre   TEXT   NOT NULL,
                             CONSTRAINT fk_book_genres_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE TABLE tags (
                      id   BIGSERIAL PRIMARY KEY,
                      name TEXT NOT NULL UNIQUE
);

CREATE TABLE book_tags (
                           id      BIGSERIAL PRIMARY KEY,
                           book_id BIGINT NOT NULL,
                           tag_id  BIGINT NOT NULL,
                           CONSTRAINT fk_book_tags_book FOREIGN KEY (book_id) REFERENCES books(id)  ON DELETE CASCADE,
                           CONSTRAINT fk_book_tags_tag  FOREIGN KEY (tag_id)  REFERENCES tags(id)   ON DELETE CASCADE,
                           CONSTRAINT uk_book_tag UNIQUE (book_id, tag_id)
);

CREATE TABLE book_chapters (
                               id                  BIGSERIAL PRIMARY KEY,
                               book_id             BIGINT  NOT NULL,
                               chapter_number      INTEGER NOT NULL,
                               title               TEXT,
                               content             TEXT    NOT NULL,
                               analysis_completed  BOOLEAN NOT NULL DEFAULT FALSE,
                               char_count          INTEGER,
                               char_count_clean    INTEGER,
                               word_count          INTEGER,
                               token_count         INTEGER,
                               ner_result          JSONB,
                               CONSTRAINT fk_chapters_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE TABLE characters (
                                  id   BIGSERIAL PRIMARY KEY,
                                  name TEXT NOT NULL UNIQUE
);

CREATE INDEX idx_characters_name_ci ON characters (lower(name));

CREATE TABLE book_characters (
                                 id             BIGSERIAL PRIMARY KEY,
                                 book_id        BIGINT  NOT NULL,
                                 character_id   BIGINT  NOT NULL,
                                 mention_count  INTEGER NOT NULL DEFAULT 0,
                                 role           TEXT,
                                 CONSTRAINT fk_book_characters_book      FOREIGN KEY (book_id)      REFERENCES books(id)            ON DELETE CASCADE,
                                 CONSTRAINT fk_book_characters_character FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
                                 CONSTRAINT uk_book_character UNIQUE (book_id, character_id)
);

CREATE TABLE character_relations (
                                     id         BIGSERIAL PRIMARY KEY,
                                     book_id    BIGINT NOT NULL,
                                     source_id  BIGINT NOT NULL,
                                     target_id  BIGINT NOT NULL,
                                     relation   TEXT,
                                     evidence   TEXT,
                                     confidence DOUBLE PRECISION,
                                     CONSTRAINT fk_char_relations_book   FOREIGN KEY (book_id)   REFERENCES books(id)            ON DELETE CASCADE,
                                      CONSTRAINT fk_char_relations_source FOREIGN KEY (source_id) REFERENCES characters(id),
                                      CONSTRAINT fk_char_relations_target FOREIGN KEY (target_id) REFERENCES characters(id),
                                     CONSTRAINT uk_character_relation UNIQUE (book_id, source_id, target_id)
);

CREATE TABLE user_books (
                            id         BIGSERIAL PRIMARY KEY,
                            user_id    BIGINT NOT NULL,
                            book_id    BIGINT NOT NULL,
                            status     TEXT   NOT NULL DEFAULT 'WANT_TO_READ',
                            created_at TIMESTAMPTZ NOT NULL,
                            CONSTRAINT fk_user_books_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            CONSTRAINT fk_user_books_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                            CONSTRAINT uk_user_book UNIQUE (user_id, book_id)
);

CREATE TABLE reviews (
                         id         BIGSERIAL PRIMARY KEY,
                         book_id    BIGINT  NOT NULL,
                         user_id    BIGINT  NOT NULL,
                         rating     INTEGER NOT NULL,
                         content    TEXT,
                         created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                         CONSTRAINT fk_reviews_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                         CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                         CONSTRAINT uk_review UNIQUE (book_id, user_id),
                         CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 5)
);
