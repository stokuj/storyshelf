from __future__ import annotations

from itertools import combinations
import re

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback when optional dep is missing
    tiktoken = None


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
TOKENIZER_NAME = "cl100k_base"
_TOKENIZER = None


def _get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None and tiktoken is not None:
        _TOKENIZER = tiktoken.get_encoding(TOKENIZER_NAME)
    return _TOKENIZER


def analyse_text(text: str) -> dict:
    """Return analysed text: counts chars, words and tokens."""

    char_count = len(text)
    word_count = len(text.split())
    # TODO: count chars with and without spaces, punctuation, etc. for more detailed analysis
    tokenizer = _get_tokenizer()
    if tokenizer is None:
        token_count = len(text) // 4
    else:
        token_count = len(tokenizer.encode(text))

    return {
        "char_count": char_count,
        "word_count": word_count,
        "token_count": token_count,
    }


def find_sentences_with_both_characters(
    content: str, characters: list[str], include_empty: bool = False
) -> list[dict]:
    """Return sentences containing each character pair from the entire book."""

    # Split text into sentences.
    sentences = [part for part in SENTENCE_SPLIT_RE.split(content.strip()) if part]
    result: list[dict] = []

    for person_a, person_b in combinations(characters, 2):
        pattern_a = re.compile(re.escape(person_a), re.IGNORECASE)
        pattern_b = re.compile(re.escape(person_b), re.IGNORECASE)
        matching = [s for s in sentences if pattern_a.search(s) and pattern_b.search(s)]

        if include_empty or matching:
            result.append({"pair": [person_a, person_b], "sentences": matching})

    return result
