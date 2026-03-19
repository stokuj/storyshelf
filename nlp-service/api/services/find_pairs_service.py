"""Find-pairs service — shared logic for HTTP endpoint and Kafka consumer."""

from __future__ import annotations

from api.services.book_service import find_sentences_with_both_characters
from api.services.callback_client import patch_to_spring


def process_find_pairs(
    content: str, names: list[str], chapter_id: int | str | None = None
) -> list[dict]:
    """Find sentence pairs and optionally send the result back to Spring.

    Args:
        content: Raw text to search.
        names: Character names to pair up.
        chapter_id: If provided, PATCHes the result to the Spring backend.

    Returns:
        List of ``{"pair": [...], "sentences": [...]}`` dicts.
    """
    result = find_sentences_with_both_characters(content, names)

    if chapter_id is not None:
        patch_to_spring(chapter_id, "find-pairs-result", {"pairs": result})

    return result
