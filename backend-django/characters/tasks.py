from celery import shared_task
from django.conf import settings

from .ai import generate_characters
from .models import CharacterAnalysis
from .services import store_characters


@shared_task
def generate_characters_task(book_id: int) -> None:
    analysis = CharacterAnalysis.objects.select_related("book").get(book_id=book_id)
    analysis.status = CharacterAnalysis.Status.RUNNING
    analysis.error_message = ""
    analysis.save(update_fields=["status", "error_message", "updated_at"])

    try:
        data = generate_characters(analysis.book)
        store_characters(analysis.book, data)
    except Exception as exc:  # CharacterGenerationError + any unexpected failure
        analysis.status = CharacterAnalysis.Status.FAILED
        analysis.error_message = str(exc)[:2000]
        analysis.save(update_fields=["status", "error_message", "updated_at"])
        return

    analysis.status = CharacterAnalysis.Status.DONE
    analysis.model = settings.OPENROUTER_MODEL
    analysis.error_message = ""
    analysis.save(update_fields=["status", "model", "error_message", "updated_at"])
