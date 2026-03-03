"""spaCy and input file helpers for character extraction."""

from __future__ import annotations

from collections import Counter
import logging
import time
from typing import Any

import spacy

from .book import Book


logger = logging.getLogger(__name__)


def extract_characters_from_chapter(
    book: Book,
    chapter_number: int = 1,
    model_name: str = "en_core_web_sm",
) -> dict[str, Any]:
    """Extract PERSON entities from a single chapter and count occurrences."""

    chapters = book.chapters or ([book.text.strip()] if book.text.strip() else [])
    if not chapters:
        return {}

    if chapter_number < 1 or chapter_number > len(chapters):
        raise ValueError(
            f"Chapter number must be in range 1..{len(chapters)} (got {chapter_number})."
        )

    chapter_text = chapters[chapter_number - 1]
    start_time = time.perf_counter()
    try:
        nlp = spacy.load(model_name)
    except OSError as error:
        raise RuntimeError(
            f"spaCy model '{model_name}' is not installed. "
            "Install project dependencies (including models) with `uv sync`."
        ) from error

    doc = nlp(chapter_text)
    people = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    counts = Counter(name for name in people if name)
    elapsed_seconds = time.perf_counter() - start_time
    logger.info(
        "Model %s chapter %d execution time: %.3f s",
        model_name,
        chapter_number,
        elapsed_seconds,
    )

    sorted_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    return {
        "model_name": model_name,
        "chapter_number": chapter_number,
        "execution_time_seconds": round(elapsed_seconds, 3),
        "characters": sorted_counts,
    }
