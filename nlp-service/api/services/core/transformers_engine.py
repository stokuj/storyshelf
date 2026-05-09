from __future__ import annotations

from collections import Counter
import logging
import os
import time
from typing import Any, Callable, cast

from transformers import pipeline

from api.models.model import TextContentRequest
from api.config import settings


logger = logging.getLogger(__name__)
DEFAULT_NER_MODEL = settings.NER_MODEL
_NER_PIPELINES: dict[str, Any] = {}


def load_ner_model(model: str) -> bool:
    if model in _NER_PIPELINES:
        return True

    try:
        logger.info("Loading transformers NER model: %s (pid=%s)", model, os.getpid())
        _NER_PIPELINES[model] = pipeline(
            task="token-classification",
            model=model,
            aggregation_strategy="first",
            stride=128,
        )
        logger.info("Transformers NER model loaded: %s", model)
        return True
    except (OSError, EnvironmentError) as exception:
        logger.warning(
            "Transformers model '%s' is not available. Skipping. Reason: %s",
            model,
            exception,
            exc_info=True,
        )
        return False


def extract_entities(
    payload: TextContentRequest, model: str = DEFAULT_NER_MODEL
) -> dict:
    """Extract named entities (persons, organizations, locations, misc) with a transformers NER model."""

    if not load_ner_model(model):
        return {}
    ner = cast(Callable[[str], list[dict]], _NER_PIPELINES[model])

    start_time = time.perf_counter()

    entities = ner(payload.content)

    entity_group_mapping: dict[str, list[str]] = {
        "characters": [],
        "organizations": [],
        "locations": [],
        "miscellaneous": [],
    }
    group_to_key = {
        "PER": "characters",
        "PERSON": "characters",
        "ORG": "organizations",
        "LOC": "locations",
        "MISC": "miscellaneous",
    }

    for entity in entities:
        word = entity.get("word", "").strip()
        group = entity.get("entity_group")
        if group is not None:
            key = group_to_key.get(str(group))
            if word and key:
                entity_group_mapping[key].append(word)

    def sorted_counts(names: list[str], min_occurrences: int = 1) -> dict[str, int]:
        counts = Counter(names)
        filtered = {name: count for name, count in counts.items() if count >= min_occurrences}
        return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

    elapsed_seconds = time.perf_counter() - start_time

    logger.info(
        "Transformers model %s execution time: %.3f s",
        model,
        elapsed_seconds,
    )

    return {
        "engine": "transformers",
        "model_name": model,
        "characters": sorted_counts(entity_group_mapping["characters"], min_occurrences=settings.NER_MIN_OCCURRENCES),
        "organizations": sorted_counts(entity_group_mapping["organizations"], min_occurrences=settings.NER_MIN_OCCURRENCES),
        "locations": sorted_counts(entity_group_mapping["locations"], min_occurrences=settings.NER_MIN_OCCURRENCES),
        "miscellaneous": sorted_counts(entity_group_mapping["miscellaneous"], min_occurrences=1),
        "execution_time_seconds": round(elapsed_seconds, 3),
    }
