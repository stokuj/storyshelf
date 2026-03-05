#book_service.py

from __future__ import annotations
from itertools import combinations
import re
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.models.model import Book

def find_pair_sentences(db: Session, book_id: int, characters: list[str]) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    row = db.execute(
        text("SELECT content FROM books WHERE id = :book_id"),
        {"book_id": book_id},
    ).first()
    if not row:
        raise ValueError(f"Book with id={book_id} not found")
    book_content = row[0]
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", book_content.strip()) if part]

    result: list[dict] = []
    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(re.escape(person_a), re.IGNORECASE)
        pattern_b = re.compile(re.escape(person_b), re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result