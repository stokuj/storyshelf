import logging

from api.config.celery_app import celery
from api.services.relations_service import process_chapter_relations

logger = logging.getLogger(__name__)


@celery.task(name="api.relations.extract_chapter_relations_task")
def extract_chapter_relations_task(content: str, chapter_id: int | str, characters: list[str] | None = None):
    """Celery task — delegates to the shared relations service."""
    try:
        return process_chapter_relations(content, chapter_id, characters)
    except Exception as e:
        logger.error(f"Error in extract_chapter_relations_task: {e}", exc_info=True)
        raise
