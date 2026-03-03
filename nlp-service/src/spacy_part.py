"""spaCy helpers for character extraction."""

from __future__ import annotations

from collections import Counter
import json
import logging
from pathlib import Path
import time

import spacy

from .book import Book


logger = logging.getLogger(__name__)

RESULTS_DIR = Path("results")


def extract_characters_from_chapter(book: Book, chapter_numbers: list[int], model: str) -> None:
    """Extract PERSON entities from chapters, count occurrences, and save results."""

    chapters = book.chapters or ([book.text.strip()] if book.text.strip() else [])
    requested = list(dict.fromkeys(chapter_numbers or [1]))

    if not requested or not chapters:
        return

    invalid = [number for number in requested if number < 1 or number > len(chapters)]
    if invalid:
        logger.warning(
            "Chapter numbers out of range 1..%d (got %s), skipping.",
            len(chapters),
            invalid,
        )
        return

    try:
        nlp = spacy.load(model)
    except OSError:
        logger.warning("spaCy model '%s' is not installed. Skipping.", model)
        return

    for chapter_number in requested:
        chapter_text = chapters[chapter_number - 1]
        start_time = time.perf_counter()
        doc = nlp(chapter_text)
        people = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        counts = Counter(name for name in people if name)
        elapsed_seconds = time.perf_counter() - start_time
        logger.info(
            "Model %s chapter %d execution time: %.3f s",
            model,
            chapter_number,
            elapsed_seconds,
        )
        sorted_counts = dict(
            sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )

        result = {
            "engine": "spacy",
            "model_name": model,
            "chapter_number": chapter_number,
            "execution_time_seconds": round(elapsed_seconds, 3),
            "characters": sorted_counts,
        }

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        file_name = f"chapter_{chapter_number}_spacy_{model.replace('/', '_')}.json"
        output_path = RESULTS_DIR / file_name
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Saved result: %s", output_path)
