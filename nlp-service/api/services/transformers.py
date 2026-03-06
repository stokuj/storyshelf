from __future__ import annotations

from collections import Counter
import logging
import time
from typing import Any, Callable, cast

from transformers import pipeline

from ..models.model import Book


logger = logging.getLogger(__name__)
DEFAULT_NER_MODEL = "dbmdz/bert-large-cased-finetuned-conll03-english"
_NER_PIPELINES: dict[str, Any] = {}


def load_ner_model(model: str) -> bool:
    if model in _NER_PIPELINES:
        return True

    try:
        logger.info("Loading transformers NER model: %s", model)
        _NER_PIPELINES[model] = pipeline(
            task="token-classification",
            model=model,
            aggregation_strategy="first",
            stride=128,
        )
        logger.info("Transformers NER model loaded: %s", model)
        return True
    except Exception:
        logger.warning("Transformers model '%s' is not available. Skipping.", model)
        return False


def is_ner_model_loaded(model: str = DEFAULT_NER_MODEL) -> bool:
    return model in _NER_PIPELINES


def extract_characters_from_book(book: Book, model: str = DEFAULT_NER_MODEL) -> dict:
    """Extract PERSON entities from chapter with a transformers NER model."""

    if not load_ner_model(model):
        return {}
    ner = cast(Callable[[str], list[dict]], _NER_PIPELINES[model])

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
        "Transformers model %s execution time: %.3f s",
        model,
        elapsed_seconds,
    )

    return {
        "engine": "transformers",
        "model_name": model,
        "characters": dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)),
        "execution_time_seconds": round(elapsed_seconds, 3),
    }
