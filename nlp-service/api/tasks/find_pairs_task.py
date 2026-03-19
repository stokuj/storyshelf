import logging

from api.config.celery_app import celery
from api.services.find_pairs_service import process_find_pairs

logger = logging.getLogger(__name__)


@celery.task(name="api.find_pairs.process_find_pairs_task")
def find_pairs_task(content: str, names: list[str], book_id: int | str | None = None):
    try:
        return process_find_pairs(content, names, book_id=book_id)
    except Exception as exc:
        logger.error("Error in find_pairs_task: %s", exc, exc_info=True)
        raise
