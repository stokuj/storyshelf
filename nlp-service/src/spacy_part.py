"""spaCy and input file helpers for character extraction."""

from __future__ import annotations

from collections import Counter
import logging
import re
import time

import spacy


logger = logging.getLogger(__name__)


def chapter_texts(book_text: str) -> list[str]:
    """Split book text into chapters using chapter headings."""
    pattern = re.compile(r"(?im)^\s*(chapter|rozdzia[łl])\b.*$")
    matches = list(pattern.finditer(book_text))

    if not matches:
        return [book_text.strip()] if book_text.strip() else []

    chapters: list[str] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(book_text)
        content = book_text[start:end].strip()
        if content:
            chapters.append(content)

    return chapters


def extract_characters_from_chapter(
    book_text: str,
    chapter_number: int = 1,
    model_name: str = "en_core_web_sm",
) -> dict[str, int]:
    """Extract PERSON entities from a single chapter and count occurrences."""

    chapters = chapter_texts(book_text)
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
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
