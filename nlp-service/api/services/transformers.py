from __future__ import annotations

from collections import Counter
import logging
import time

from transformers import pipeline

from ..models.model import BookChapter, Book


logger = logging.getLogger(__name__)


def extract_characters_from_book(book: Book, model: str) -> dict:
    """Extract PERSON entities from chapter with a transformers NER model."""

    try:
        ner = pipeline(
            task="token-classification",
            model=model,
            aggregation_strategy="first",
            stride=128,
        )
    except Exception:
        logger.warning("Transformers model '%s' is not available. Skipping.", model)
        return {}

    start_time = time.perf_counter()

    entities = ner(book.content)
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
        elapsed_seconds,
    )

    return {
        "engine": "transformers",
        "model_name": model,
        "characters": dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)),
        "execution_time_seconds": round(elapsed_seconds, 3),
    }