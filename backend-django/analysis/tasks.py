from celery import shared_task
from django.db import transaction
from django.db.models import F


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyse_chapter(self, chapter_id: int, content: str):
    from books.models import Chapter
    from .text_stats import analyse_text

    chapter = Chapter.objects.get(id=chapter_id)
    if chapter.analysis_completed:
        return

    stats = analyse_text(content)
    chapter.char_count = stats["char_count"]
    chapter.char_count_clean = stats["char_count_clean"]
    chapter.word_count = stats["word_count"]
    chapter.token_count = stats["token_count"]
    chapter.analysis_completed = True
    chapter.save()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def ner_chapter(self, chapter_id: int, content: str):
    from books.models import Book, Chapter
    from .ner_engine import extract_entities

    chapter = Chapter.objects.select_related("book").get(id=chapter_id)
    if chapter.ner_pending is not None:
        return

    result = extract_entities(content)
    chapter.ner_pending = result
    chapter.save(update_fields=["ner_pending"])

    Book.objects.filter(id=chapter.book_id).update(
        ner_completed_count=F("ner_completed_count") + 1
    )

    book = Book.objects.get(id=chapter.book_id)
    if book.ner_completed_count >= book.chapters_count:
        merge_book_ner.delay(book.id)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def merge_book_ner(self, book_id: int):
    from books.models import Book, Chapter
    from .models import BookCharacter, BookPlace, BookOrganization

    book = Book.objects.prefetch_related("chapters").get(id=book_id)
    chapters = list(book.chapters.all())

    char_totals: dict[str, int] = {}
    place_totals: dict[str, int] = {}
    org_totals: dict[str, int] = {}
    full_text_parts: list[str] = []

    for chapter in chapters:
        if chapter.text:
            full_text_parts.append(chapter.text)
        if not chapter.ner_pending:
            continue
        for name, count in chapter.ner_pending.get("characters", {}).items():
            char_totals[name] = char_totals.get(name, 0) + count
        for name, count in chapter.ner_pending.get("locations", {}).items():
            place_totals[name] = place_totals.get(name, 0) + count
        for name, count in chapter.ner_pending.get("organizations", {}).items():
            org_totals[name] = org_totals.get(name, 0) + count

    with transaction.atomic():
        for name, total in char_totals.items():
            char, created = BookCharacter.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                char.mention_count = F("mention_count") + total
                char.save(update_fields=["mention_count"])

        for name, total in place_totals.items():
            place, created = BookPlace.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                place.mention_count = F("mention_count") + total
                place.save(update_fields=["mention_count"])

        for name, total in org_totals.items():
            org, created = BookOrganization.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                org.mention_count = F("mention_count") + total
                org.save(update_fields=["mention_count"])

        chapters_to_update = Chapter.objects.filter(book_id=book_id)
        chapters_to_update.update(text="", ner_pending=None)

    full_text = " ".join(full_text_parts)
    character_names = list(char_totals.keys())

    if full_text and len(character_names) >= 2:
        find_pairs.delay(book_id, full_text, character_names)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def find_pairs(self, book_id: int, full_text: str, character_names: list[str]):
    from .text_parser import find_sentences_with_both_characters

    pairs_data = find_sentences_with_both_characters(full_text, character_names)
    if not pairs_data:
        return

    relations_for_book(book_id, pairs_data)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def relations_for_book(self, book_id: int, pairs_data: list[dict]):
    import json
    from .models import BookCharacter, CharacterRelationship
    from .llm_engine import llm_service

    total_relations = 0
    for item in pairs_data:
        pair = item["pair"]
        sentences = item["sentences"]
        if not sentences:
            continue
        result_json = llm_service.extract_relations_sync(pair, sentences)
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            continue
        for rel in result.get("relations", []):
            try:
                source = BookCharacter.objects.get(name=rel["source"])
                target = BookCharacter.objects.get(name=rel["target"])
                CharacterRelationship.objects.get_or_create(
                    from_character=source,
                    to_character=target,
                    book_id=book_id,
                    defaults={"relation_type": rel["relation"]},
                )
                total_relations += 1
            except BookCharacter.DoesNotExist:
                continue
