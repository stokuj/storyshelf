from __future__ import annotations

from itertools import combinations
import re

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def find_sentences_with_both_characters(
    content: str, characters: list[str], include_empty: bool = False
) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    # Split text into sentences.
    sentences = [part for part in SENTENCE_SPLIT_RE.split(content.strip()) if part]
    result: list[dict] = []

    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(r"\b" + re.escape(person_a) + r"\b", re.IGNORECASE)
        pattern_b = re.compile(r"\b" + re.escape(person_b) + r"\b", re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if include_empty or matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result
