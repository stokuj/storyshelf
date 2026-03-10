# book_service.py

from __future__ import annotations

from itertools import combinations
import re


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def analyse_text(text: str) -> dict:
    """Return analysed text: counts chars, words and tokens."""

    char_count = len(text)
    word_count = len(text.split())
    #TODO: count chars with and without spaces, punctuation, etc. for more detailed analysis
    #TODO: change to real tokenizer
    token_count = len(text) // 4

    return {
        "char_count": char_count,
        "word_count": word_count,
        "token_count": token_count,
    }


def find_sentences_with_both_characters(content: str, characters: list[str], include_empty: bool = False) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    # Dzieli tekst na zdania.
    sentences = [part for part in SENTENCE_SPLIT_RE.split(content.strip()) if part]
    result: list[dict] = []


    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(re.escape(person_a), re.IGNORECASE)
        pattern_b = re.compile(re.escape(person_b), re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if include_empty or matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result
