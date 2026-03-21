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

INSERT INTO characters (name)
SELECT DISTINCT trim(name)
FROM books b
JOIN LATERAL jsonb_each_text(b.characters) AS c(name, count) ON TRUE
WHERE b.characters IS NOT NULL
  AND trim(name) <> ''
ON CONFLICT (name) DO NOTHING;

INSERT INTO characters (name)
SELECT DISTINCT trim(name)
FROM books b
JOIN LATERAL jsonb_array_elements(b.find_pairs_result->'pairs') AS p(pair) ON TRUE
JOIN LATERAL jsonb_array_elements_text(p.pair->'pair') AS name ON TRUE
WHERE b.find_pairs_result IS NOT NULL
  AND trim(name) <> ''
ON CONFLICT (name) DO NOTHING;

INSERT INTO characters (name)
SELECT DISTINCT trim(name)
FROM books b
JOIN LATERAL jsonb_array_elements(b.relations_result->'all_relations') AS ar(item) ON TRUE
JOIN LATERAL jsonb_array_elements_text(ar.item->'pair') AS name ON TRUE
WHERE b.relations_result IS NOT NULL
  AND trim(name) <> ''
ON CONFLICT (name) DO NOTHING;

INSERT INTO characters (name)
SELECT DISTINCT trim(rel->>'source')
FROM books b
JOIN LATERAL jsonb_array_elements(b.relations_result->'all_relations') AS ar(item) ON TRUE
JOIN LATERAL jsonb_array_elements(ar.item->'relations'->'relations') AS rel ON TRUE
WHERE b.relations_result IS NOT NULL
  AND trim(rel->>'source') <> ''
ON CONFLICT (name) DO NOTHING;

INSERT INTO characters (name)
SELECT DISTINCT trim(rel->>'target')
FROM books b
JOIN LATERAL jsonb_array_elements(b.relations_result->'all_relations') AS ar(item) ON TRUE
JOIN LATERAL jsonb_array_elements(ar.item->'relations'->'relations') AS rel ON TRUE
WHERE b.relations_result IS NOT NULL
  AND trim(rel->>'target') <> ''
ON CONFLICT (name) DO NOTHING;

INSERT INTO book_characters (book_id, character_id, mention_count)
SELECT b.id,
       c.id,
       COALESCE(NULLIF(cdata.count, '')::INTEGER, 0)
FROM books b
JOIN LATERAL jsonb_each_text(b.characters) AS cdata(name, count) ON TRUE
JOIN characters c ON lower(c.name) = lower(trim(cdata.name))
WHERE b.characters IS NOT NULL
  AND trim(cdata.name) <> ''
ON CONFLICT (book_id, character_id) DO UPDATE
SET mention_count = EXCLUDED.mention_count;

INSERT INTO character_relations (book_id, source_id, target_id)
SELECT b.id,
       cs.id,
       ct.id
FROM books b
JOIN LATERAL jsonb_array_elements(b.find_pairs_result->'pairs') AS p(pair) ON TRUE
JOIN characters cs ON lower(cs.name) = lower(trim(p.pair->'pair'->>0))
JOIN characters ct ON lower(ct.name) = lower(trim(p.pair->'pair'->>1))
WHERE b.find_pairs_result IS NOT NULL
  AND trim(p.pair->'pair'->>0) <> ''
  AND trim(p.pair->'pair'->>1) <> ''
ON CONFLICT (book_id, source_id, target_id) DO NOTHING;

INSERT INTO character_relations (book_id, source_id, target_id, relation, evidence, confidence)
SELECT b.id,
       cs.id,
       ct.id,
       NULLIF(trim(rel->>'relation'), ''),
       NULLIF(trim(rel->>'evidence'), ''),
       CASE
           WHEN rel ? 'confidence' THEN NULLIF(rel->>'confidence', '')::DOUBLE PRECISION
           ELSE NULL
       END
FROM books b
JOIN LATERAL jsonb_array_elements(b.relations_result->'all_relations') AS ar(item) ON TRUE
JOIN LATERAL jsonb_array_elements(ar.item->'relations'->'relations') AS rel ON TRUE
JOIN characters cs ON lower(cs.name) = lower(trim(rel->>'source'))
JOIN characters ct ON lower(ct.name) = lower(trim(rel->>'target'))
WHERE b.relations_result IS NOT NULL
  AND trim(rel->>'source') <> ''
  AND trim(rel->>'target') <> ''
ON CONFLICT (book_id, source_id, target_id) DO UPDATE
SET relation = EXCLUDED.relation,
    evidence = EXCLUDED.evidence,
    confidence = EXCLUDED.confidence;

ALTER TABLE books
    DROP COLUMN characters,
    DROP COLUMN find_pairs_result,
    DROP COLUMN relations_result;
