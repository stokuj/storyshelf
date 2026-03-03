"""Transformers helpers for character extraction."""

from __future__ import annotations

from collections import Counter
import logging
import time
from typing import Any

from transformers import pipeline

from .book import Book


logger = logging.getLogger(__name__)


def extract_chars(book: Book, chapter_numbers: list[int] | None = None, model: str = "dslim/bert-base-NER",) -> list[dict[str, Any]]:
    """Extract person entities from one or many chapters with a transformers NER model."""

    chapters = book.chapters or ([book.text.strip()] if book.text.strip() else [])
    requested = list(dict.fromkeys(chapter_numbers or [1]))

    if not requested:
        return []

    if not chapters:
        return [
            {
                "engine": "transformers",
                "model_name": model,
                "chapter_number": number,
                "execution_time_seconds": 0.0,
                "characters": {},
            }
            for number in requested
        ]

    invalid = [number for number in requested if number < 1 or number > len(chapters)]
    if invalid:
        raise ValueError(f"Chapter numbers must be in range 1..{len(chapters)} (got {invalid}).")

    try:
        ner = pipeline(task="token-classification", model=model, aggregation_strategy="simple")
    except Exception as error:
        raise RuntimeError(f"Transformers model '{model}' is not available. Install dependencies with `uv sync` and verify model name.") from error

    results: list[dict[str, Any]] = []
    for chapter_number in requested:
        chapter_text = chapters[chapter_number - 1]
        start_time = time.perf_counter()
        entities = ner(chapter_text)
        persons = [
            entity["word"].strip()
            for entity in entities
            if entity.get("entity_group") in {"PER", "PERSON"} and entity.get("word")
        ]
        counts = Counter(name for name in persons if name)
        elapsed_seconds = time.perf_counter() - start_time
        logger.info(
            "Transformers model %s chapter %d execution time: %.3f s",
            model,
            chapter_number,
            elapsed_seconds,
        )
        sorted_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

        results.append(
            {
                "engine": "transformers",
                "model_name": model,
                "chapter_number": chapter_number,
                "execution_time_seconds": round(elapsed_seconds, 3),
                "characters": sorted_counts,
            }
        )
    return results


extract_characters_from_chapter = extract_chars
