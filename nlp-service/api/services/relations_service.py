"""Relations service — shared orchestration logic for HTTP endpoint, Celery task and Kafka consumer."""

from __future__ import annotations

import asyncio
import json
import logging

from api.models.model import TextContentRequest
from api.services.book_service import find_sentences_with_both_characters
from api.services.callback_client import patch_to_spring, patch_to_spring_async
from api.services.llm_service import llm_service
from api.services.transformers_service import DEFAULT_NER_MODEL, extract_entities

logger = logging.getLogger(__name__)


def process_chapter_relations(
    content: str,
    chapter_id: int | str,
    characters: list[str] | None = None,
) -> dict:
    """Extract character relations for a whole chapter.

    Orchestration flow:
        1. Determine characters (from argument or via local NER).
        2. Find sentences containing character pairs.
        3. For each pair — call LLM to extract relations.
        4. Optionally PATCH the result back to Spring.

    Args:
        content: Full chapter text.
        chapter_id: Chapter identifier (used for logging and Spring callback).
        characters: Pre-determined character names.  If ``None`` or fewer than 2,
            NER is run locally to discover them.

    Returns:
        ``{"chapterId": ..., "all_relations": [...]}``
    """

    # 1. Determine characters ---------------------------------------------------
    if characters and len(characters) >= 2:
        logger.info("Using provided characters %s for chapter %s", characters, chapter_id)
        top_chars = characters
    else:
        logger.info("No characters provided for chapter %s, running NER locally", chapter_id)
        ner_result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)
        all_chars = list(ner_result.get("characters", {}).keys())

        if len(all_chars) < 2:
            logger.info("Not enough characters in chapter %s to find relations", chapter_id)
            return {"relations": []}

        top_chars = all_chars

    # 2. Find sentence pairs ----------------------------------------------------
    pairs_sentences = find_sentences_with_both_characters(content, top_chars)

    if not pairs_sentences:
        logger.info("No sentences found for relations in chapter %s", chapter_id)
        return {"relations": []}

    # 3. Extract relations per pair ----------------------------------------------
    all_results: list[dict] = []
    for pair_data in pairs_sentences:
        pair = pair_data["pair"]
        sentences = pair_data["sentences"]

        logger.info("Extracting relations for %s in chapter %s…", pair, chapter_id)
        relations_raw = llm_service.extract_relations_sync(pair, sentences)

        try:
            relations_data = json.loads(relations_raw)
        except json.JSONDecodeError:
            relations_data = {"raw": relations_raw}

        all_results.append({
            "pair": pair,
            "sentencesCount": len(sentences),
            "relations": relations_data,
        })

    # 4. Build final result ------------------------------------------------------
    result = {
        "chapterId": chapter_id,
        "all_relations": all_results,
    }

    # 5. Callback to Spring ------------------------------------------------------
    compat_result = {
        "pair": all_results[0]["pair"],
        "sentencesCount": sum(r["sentencesCount"] for r in all_results),
        "relations": {"all_pairs": all_results},
    }

    patch_to_spring(chapter_id, "relations-result", compat_result)

    logger.info("Successfully sent relations result for chapter %s back to Spring", chapter_id)
    return result


async def process_book_relations_async(pairs: list[dict], book_id: int | str) -> dict:
    async def extract_one(pair_data: dict) -> dict:
        pair = pair_data["pair"]
        sentences = pair_data["sentences"]
        relations_raw = await llm_service.extract_relations(pair, sentences)
        try:
            relations = json.loads(relations_raw)
        except json.JSONDecodeError:
            relations = {"raw": relations_raw}
        return {"pair": pair, "relations": relations}

    results = await asyncio.gather(*[extract_one(p) for p in pairs])

    result = {"bookId": book_id, "all_relations": list(results)}
    await patch_to_spring_async(book_id, "relations-result", result, resource="books")
    return result
