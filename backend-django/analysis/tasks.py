import json
import logging

from celery import shared_task
from django.db import transaction

from .ner_engine import extract_entities_from_chunks
from .text_parser import find_sentences_with_both_characters

try:
    import openai

    from .llm_engine import llm_service
except ImportError:  # pragma: no cover
    openai = None  # type: ignore[assignment]
    llm_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


@shared_task
def analyse_book(book_id: int):
    """Run NER on Book.text, save per-book entities, dispatch LLM task.

    Idempotent: deletes existing entities before writing new ones so re-runs
    on updated text don't accumulate stale entries.
    """
    from books.models import Book

    from .models import BookCharacter, BookOrganization, BookPlace

    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        logger.warning("analyse_book: Book %s does not exist", book_id)
        return
    if not book.text:
        return

    full_text = book.text
    result = extract_entities_from_chunks(full_text)

    char_names: list[str] = []
    with transaction.atomic():
        BookCharacter.objects.filter(book=book).delete()
        BookPlace.objects.filter(book=book).delete()
        BookOrganization.objects.filter(book=book).delete()

        for name, count in result.get("characters", {}).items():
            BookCharacter.objects.create(name=name, book=book, mention_count=count)
            char_names.append(name)

        for name, count in result.get("locations", {}).items():
            BookPlace.objects.create(name=name, book=book, mention_count=count)

        for name, count in result.get("organizations", {}).items():
            BookOrganization.objects.create(name=name, book=book, mention_count=count)

    pairs_data = find_sentences_with_both_characters(full_text, char_names)

    if pairs_data and len(char_names) >= 2:
        Book.objects.filter(id=book_id).update(text="")
        relations_for_book.delay(book_id, pairs_data)
    else:
        Book.objects.filter(id=book_id).update(text="")


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
        except (json.JSONDecodeError, openai.OpenAIError) as e:
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
