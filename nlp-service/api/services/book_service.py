#book_service.py

from __future__ import annotations

from itertools import combinations
from pathlib import Path
import re

from api.models.model import Book

def find_pair_sentences(book: Book, characters: list[str]) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    sentences = [part for part in re.split(r"(?<=[.!?])\s+", book.content.strip()) if part]

    result: list[dict] = []
    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(re.escape(person_a), re.IGNORECASE)
        pattern_b = re.compile(re.escape(person_b), re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result