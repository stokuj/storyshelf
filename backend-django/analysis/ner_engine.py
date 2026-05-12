from __future__ import annotations

from collections import Counter
import logging
import os
import time
from typing import Any, Callable, cast

from transformers import pipeline

logger = logging.getLogger(__name__)
DEFAULT_NER_MODEL = os.getenv(
    "NER_MODEL", "dbmdz/bert-large-cased-finetuned-conll03-english"
)
NER_MIN_OCCURRENCES = int(os.getenv("NER_MIN_OCCURRENCES", "5"))
_NER_PIPELINES: dict[str, Any] = {}


def load_ner_model(model: str) -> bool:
    if model in _NER_PIPELINES:
        return True
    try:
        logger.info("Loading NER model: %s (pid=%s)", model, os.getpid())
        _NER_PIPELINES[model] = pipeline(
            task="token-classification",
            model=model,
            aggregation_strategy="first",
            stride=128,
        )
        logger.info("NER model loaded: %s", model)
        return True
    except (OSError, EnvironmentError) as exc:
        logger.warning("Model '%s' unavailable: %s", model, exc)
        return False


def extract_entities(text: str, model: str = DEFAULT_NER_MODEL) -> dict:
    """Extract named entities from text.

    Returns dict: {characters, organizations, locations, miscellaneous}.
    Each value is {name: count} sorted by count descending.
    MISC is always empty dict — ignored per project spec.
    """
    if not load_ner_model(model):
        return {}

    ner = cast(Callable[[str], list[dict]], _NER_PIPELINES[model])
    start_time = time.perf_counter()
    entities = ner(text)

    group_map: dict[str, list[str]] = {
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
                group_map[key].append(word)

    def sorted_counts(names: list[str], min_occ: int = 1) -> dict[str, int]:
        counts = Counter(names)
        filtered = {n: c for n, c in counts.items() if c >= min_occ}
        return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

    elapsed = time.perf_counter() - start_time
    logger.info("NER execution: %.3f s", elapsed)

    return {
        "engine": "transformers",
        "model_name": model,
        "characters": sorted_counts(group_map["characters"], NER_MIN_OCCURRENCES),
        "organizations": sorted_counts(group_map["organizations"], NER_MIN_OCCURRENCES),
        "locations": sorted_counts(group_map["locations"], NER_MIN_OCCURRENCES),
        "miscellaneous": {},
        "execution_time_seconds": round(elapsed, 3),
    }
