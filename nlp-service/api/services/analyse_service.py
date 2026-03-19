"""Analyse service — shared logic for HTTP endpoint and Kafka consumer."""

from __future__ import annotations

from api.services.book_service import analyse_text
from api.services.callback_client import patch_to_spring


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
        patch_to_spring(chapter_id, "analyse-result", {"analysis": result})

    return result
