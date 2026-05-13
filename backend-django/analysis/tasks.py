import json
import logging

from celery import shared_task
from django.db import transaction

from .ner_engine import extract_entities_from_chunks
from .text_parser import find_sentences_with_both_characters

try:
    from .llm_engine import llm_service
except Exception:  # pragma: no cover
    llm_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@shared_task
def analyse_book(book_id: int):
    """Run NER on Book.text, save per-book entities, dispatch LLM task.

    Note: re-running after a text update accumulates entities (no delete-before-recreate).
    Clear BookCharacter/Place/Organization manually if a clean re-analysis is needed.
    """
    from books.models import Book

    from .models import BookCharacter, BookOrganization, BookPlace

    book = Book.objects.get(id=book_id)
    if not book.text:
        return

    full_text = book.text
    result = extract_entities_from_chunks(full_text)

    char_names: list[str] = []
    with transaction.atomic():
        for name, count in result.get("characters", {}).items():
            BookCharacter.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )
            char_names.append(name)

        for name, count in result.get("locations", {}).items():
            BookPlace.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )

        for name, count in result.get("organizations", {}).items():
            BookOrganization.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )

    pairs_data = find_sentences_with_both_characters(full_text, char_names)
    Book.objects.filter(id=book_id).update(text="")

    if pairs_data and len(char_names) >= 2:
        relations_for_book.delay(book_id, pairs_data)


@shared_task
def relations_for_book(book_id: int, pairs_data: list[dict]):
    """Extract character relationships via LLM for each co-occurring pair.

    Errors per pair are logged and skipped — the task never retries.
    """
    if llm_service is None:  # openai unavailable at import time
        logger.error("relations_for_book: llm_service unavailable, skipping book %s", book_id)
        return

    from .models import BookCharacter, CharacterRelationship

    valid_relation_types = {r.value for r in CharacterRelationship.RelationType}

    for item in pairs_data:
        pair = item["pair"]
        sentences = item["sentences"]
        if not sentences:
            continue
        try:
            result_json = llm_service.extract_relations(pair, sentences)
            result = json.loads(result_json)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("LLM error for pair %s: %s", pair, e, exc_info=True)
            continue

        for rel in result.get("relations", []):
            relation_type = rel.get("relation", "")
            if relation_type not in valid_relation_types:
                logger.warning("Unknown relation type '%s', skipping", relation_type)
                continue
            try:
                source = BookCharacter.objects.get(name=rel["source"], book_id=book_id)
                target = BookCharacter.objects.get(name=rel["target"], book_id=book_id)
                CharacterRelationship.objects.get_or_create(
                    from_character=source,
                    to_character=target,
                    book_id=book_id,
                    defaults={"relation_type": relation_type},
                )
            except BookCharacter.DoesNotExist:
                logger.warning("Character not found for relation: %s", rel)
                continue
