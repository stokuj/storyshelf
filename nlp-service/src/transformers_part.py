"""Transformers helpers for character extraction."""

from __future__ import annotations

from collections import Counter
import json
import logging
from pathlib import Path
import time

from transformers import pipeline

from .book import Book


logger = logging.getLogger(__name__)

RESULTS_DIR = Path("results")


def extract_characters_from_chapter(book: Book, chapter_numbers: list[int], model: str) -> None:
    """Extract PERSON entities from chapters with a transformers NER model and save results."""

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
        ner = pipeline(task="token-classification", model=model, aggregation_strategy="simple")
    except Exception:
        logger.warning("Transformers model '%s' is not available. Skipping.", model)
        return


    # MAIN LOOP
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
        sorted_counts = dict(
            sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )

        result = {
            "engine": "transformers",
            "model_name": model,
            "chapter_number": chapter_number,
            "execution_time_seconds": round(elapsed_seconds, 3),
            "characters": sorted_counts,
        }

        file_name = (
            f"chapter_{chapter_number}_transformers_{model.replace('/', '_')}.json"
        )
        output_path = RESULTS_DIR / file_name
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Saved result: %s", output_path)
