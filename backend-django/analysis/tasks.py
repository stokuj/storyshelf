import json
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .ner_engine import extract_entities_from_chunks
from .text_parser import find_sentences_with_both_characters

try:
    import openai

    from .llm_engine import llm_service
except ImportError:  # pragma: no cover
    openai = None  # type: ignore[assignment]
    llm_service = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _upsert_characters(book, entities: dict) -> list[str]:
    from .models import BookCharacter

    existing = {c.slug: c for c in BookCharacter.objects.filter(book=book)}
    char_names: list[str] = []
    used_slugs_this_run: set[str] = set()

    for name, count in entities.items():
        base = slugify(name)[:200] or "character"
        slug = base
        counter = 2
        while slug in used_slugs_this_run:
            slug = f"{base}-{counter}"
            counter += 1
        used_slugs_this_run.add(slug)

        if slug in existing:
            char = existing[slug]
            char.mention_count = count
            char.save(update_fields=["mention_count"])
        else:
            BookCharacter.objects.create(
                book=book,
                name=name,
                slug=slug,
                mention_count=count,
                source="ai",
                confidence=None,
                is_hidden=False,
            )
        char_names.append(name)

    return char_names


@shared_task
def analyse_book(book_id: int):
    """Run NER on Book.text, upsert per-book entities (preserving admin flags), dispatch LLM."""
    from books.models import Book

    from .models import BookOrganization, BookPlace

    try:
        book = Book.objects.get(id=book_id)
    except Book.DoesNotExist:
        logger.warning("analyse_book: Book %s does not exist", book_id)
        return
    if not book.text:
        return

    Book.objects.filter(id=book_id).update(
        ai_extraction_status="running",
        ai_extraction_started_at=timezone.now(),
        ai_extraction_failure_reason="",
    )

    try:
        full_text = book.text
        result = extract_entities_from_chunks(full_text)

        with transaction.atomic():
            char_names = _upsert_characters(book, result.get("characters", {}))

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

        Book.objects.filter(id=book_id).update(
            ai_extraction_status="done",
            ai_extraction_finished_at=timezone.now(),
        )

    except Exception as exc:
        Book.objects.filter(id=book_id).update(
            ai_extraction_status="failed",
            ai_extraction_finished_at=timezone.now(),
            ai_extraction_failure_reason=str(exc)[:512],
        )
        raise


@shared_task
def relations_for_book(book_id: int, pairs_data: list[dict]):
    """Extract character relationships via LLM for each co-occurring pair.

    Errors per pair are logged and skipped — the task never retries.
    """
    if llm_service is None:
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
