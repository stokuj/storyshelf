import logging
import httpx
from api.config import settings
from api.config.celery_app import celery
from api.models.model import TextContentRequest
from api.services.transformers_service import DEFAULT_NER_MODEL, extract_entities

logger = logging.getLogger(__name__)

@celery.task(name="api.ner.extract_entities_task")
def extract_entities_task(content: str, chapter_id: int | str | None = None):
    try:
        result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)
        
        # If triggered via Kafka, we'll have a chapter_id to send the result back to Spring
        if chapter_id is not None:
            patch_url = f"{settings.SPRINGSHELF_BASE_URL}/api/fastAPI/chapters/{chapter_id}/ner-result"
            logger.info(f"NER task complete for chapter {chapter_id}, sending PATCH to {patch_url}")
            
            response = httpx.patch(patch_url, json=result, timeout=30.0)
            response.raise_for_status()
            logger.info(f"Successfully sent NER result for chapter {chapter_id} back to Spring")
            
        return result
    except Exception as e:
        logger.error(f"Error in extract_entities_task: {e}", exc_info=True)
        raise
