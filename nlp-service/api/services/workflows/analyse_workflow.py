"""Analyse service — shared logic for HTTP endpoint and Kafka consumer."""

from __future__ import annotations

from api.services.core.text_stats import analyse_text
from api.kafka.producer import TOPIC_ANALYSE_RESULTS, send_json


def process_analyse(content: str, chapter_id: int | str | None = None) -> dict:
    """Analyse text and optionally send the result back to Spring.

    Args:
        content: Raw text to analyse.
        chapter_id: If provided, PATCHes the result to the Spring backend.

    Returns:
        Analysis dict with char_count, word_count, token_count, etc.
    """
    result = analyse_text(content)

    if chapter_id is not None:
        send_json(
            TOPIC_ANALYSE_RESULTS,
            str(chapter_id),
            {"chapterId": chapter_id, "analysis": result},
        )

    return result
