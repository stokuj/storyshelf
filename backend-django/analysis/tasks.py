import requests
from celery import shared_task
from django.conf import settings

HTTP_TIMEOUT = 60


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyse_chapter(self, chapter_id: int, content: str):
    try:
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/chapters/{chapter_id}/analyse",
            json={"content": content},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def ner_chapter(self, chapter_id: int, content: str):
    try:
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/chapters/{chapter_id}/ner",
            json={"content": content},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def find_pairs(self, book_id: int):
    try:
        from books.models import Book, Chapter
        from analysis.models import BookCharacter

        book = Book.objects.prefetch_related("chapters").get(id=book_id)
        full_text = " ".join(c.text for c in book.chapters.order_by("chapter_number"))
        characters = {bc.name: bc.mention_count for bc in BookCharacter.objects.all()}
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/books/{book_id}/find-pairs",
            json={"content": full_text, "characters": characters},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def relations_for_book(self, book_id: int):
    try:
        from analysis.models import CharacterRelationship

        pairs = list(
            CharacterRelationship.objects.filter(
                book_id=book_id, relation_type__isnull=True
            ).values_list("from_character__name", "to_character__name")
        )
        if not pairs:
            return
        resp = requests.post(
            f"{settings.NLP_SERVICE_URL}/books/{book_id}/relations",
            json={"pairs": [[s, t] for s, t in pairs]},
            timeout=HTTP_TIMEOUT,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        self.retry(exc=exc)
