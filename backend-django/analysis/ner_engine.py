from __future__ import annotations

import logging
import os
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_NER_MODEL = os.getenv("NER_MODEL", "en_core_web_trf")
NER_MIN_OCCURRENCES = int(os.getenv("NER_MIN_OCCURRENCES", "5"))

_NLP: dict[str, Any] = {}

LABEL_MAP = {
    "PERSON": "characters",
    "PER": "characters",
    "ORG": "organizations",
    "LOC": "locations",
    "GPE": "locations",
}


def _get_nlp(model: str = DEFAULT_NER_MODEL) -> Any | None:
    if model in _NLP:
        return _NLP[model]
    try:
        import spacy

        logger.info("Loading spaCy model: %s", model)
        _NLP[model] = spacy.load(model)
        logger.info("spaCy model loaded: %s", model)
        return _NLP[model]
    except (OSError, ImportError) as exc:
        logger.warning("spaCy model '%s' unavailable: %s", model, exc)
        return None


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    if chunk_size <= overlap:
        raise ValueError(f"chunk_size ({chunk_size}) must be greater than overlap ({overlap})")
    words = text.split()
    if not words:
        return []
    step = chunk_size - overlap
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_entities_from_chunks(
    text: str,
    model: str = DEFAULT_NER_MODEL,
    chunk_size: int = 400,
    overlap: int = 50,
) -> dict:
    nlp = _get_nlp(model)
    if nlp is None:
        return {"characters": {}, "organizations": {}, "locations": {}}

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return {"characters": {}, "organizations": {}, "locations": {}}

    raw: dict[str, list[str]] = {
        "characters": [],
        "organizations": [],
        "locations": [],
    }

    for doc in nlp.pipe(chunks, batch_size=8):
        for ent in doc.ents:
            key = LABEL_MAP.get(ent.label_)
            if key:
                raw[key].append(ent.text.strip())

    def filtered_counts(names: list[str]) -> dict[str, int]:
        counts = Counter(names)
        return {
            n: c
            for n, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            if c >= NER_MIN_OCCURRENCES
        }

    return {
        "characters": filtered_counts(raw["characters"]),
        "organizations": filtered_counts(raw["organizations"]),
        "locations": filtered_counts(raw["locations"]),
    }
