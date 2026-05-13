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


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def analyse_book(self, book_id: int):
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


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def relations_for_book(self, book_id: int, pairs_data: list[dict]):
    from .models import BookCharacter, CharacterRelationship

    for item in pairs_data:
        pair = item["pair"]
        sentences = item["sentences"]
        if not sentences:
            continue
        try:
            result_json = llm_service.extract_relations(pair, sentences)
            result = json.loads(result_json)
        except Exception as e:
            logger.warning("LLM error for pair %s: %s", pair, e)
            continue

        for rel in result.get("relations", []):
            try:
                source = BookCharacter.objects.get(name=rel["source"], book_id=book_id)
                target = BookCharacter.objects.get(name=rel["target"], book_id=book_id)
                CharacterRelationship.objects.get_or_create(
                    from_character=source,
                    to_character=target,
                    book_id=book_id,
                    defaults={"relation_type": rel["relation"]},
                )
            except BookCharacter.DoesNotExist:
                logger.warning("Character not found for relation: %s", rel)
                continue
