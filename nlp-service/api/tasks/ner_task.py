import logging

from api.config.celery_app import celery
from api.services.ner_service import process_ner

logger = logging.getLogger(__name__)


@celery.task(name="api.ner.extract_entities_task")
def extract_entities_task(content: str, chapter_id: int | str | None = None):
    """Celery task — delegates to the shared NER service."""
    try:
        return process_ner(content, chapter_id)
    except Exception as e:
        logger.error(f"Error in extract_entities_task: {e}", exc_info=True)
        raise
