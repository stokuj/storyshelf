# book_service.py

from __future__ import annotations

from itertools import combinations
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def get_book_content_by_id(db: Session, book_id: int) -> str | None:
    row = db.execute(
        text("SELECT content FROM books WHERE id = :book_id"),
        {"book_id": book_id},
    ).first()
    if not row:
        return None
    return row[0]


def find_pair_sentences(book_content: str, characters: list[str], include_empty: bool = False) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    # Dzieli tekst na zdania.
    sentences = [part for part in SENTENCE_SPLIT_RE.split(book_content.strip()) if part]
    result: list[dict] = []


    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(re.escape(person_a), re.IGNORECASE)
        pattern_b = re.compile(re.escape(person_b), re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if include_empty or matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result
