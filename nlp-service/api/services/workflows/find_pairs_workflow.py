"""Find-pairs service — shared logic for HTTP endpoint and Kafka consumer."""

from __future__ import annotations

from api.services.core.text_parser import find_sentences_with_both_characters
from api.kafka.producer import TOPIC_FIND_PAIRS_RESULTS, send_json


def process_find_pairs(
    content: str,
    names: list[str],
    chapter_id: int | str | None = None,
    book_id: int | str | None = None,
) -> list[dict]:
    """Find sentence pairs and optionally send the result back to Spring.

    Args:
        content: Raw text to search.
        names: Character names to pair up.
        chapter_id: If provided, PATCHes the result to the Spring backend.
        book_id: If provided, PATCHes the result to the Spring backend.

    Returns:
        List of ``{"pair": [...], "sentences": [...]}`` dicts.
    """
    result = find_sentences_with_both_characters(content, names)

    if book_id is not None:
        send_json(
            TOPIC_FIND_PAIRS_RESULTS,
            str(book_id),
            {"bookId": book_id, "pairs": result},
        )

    return result
