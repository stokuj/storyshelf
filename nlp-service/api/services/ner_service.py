"""NER service — shared logic for HTTP endpoint, Celery task and Kafka consumer."""

from __future__ import annotations

from api.models.model import TextContentRequest
from api.services.callback_client import patch_to_spring
from api.services.transformers_service import DEFAULT_NER_MODEL, extract_entities


def process_ner(content: str, chapter_id: int | str | None = None) -> dict:
    """Run NER on *content* and optionally send the result back to Spring.

    Args:
        content: Raw text to analyse.
        chapter_id: If provided, PATCHes the result to the Spring backend.

    Returns:
        NER result dict (characters, organisations, locations, etc.).
    """
    result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)

    if chapter_id is not None:
        patch_to_spring(chapter_id, "ner-result", result)

    return result
