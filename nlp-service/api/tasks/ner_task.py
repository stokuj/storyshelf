
from api.config.celery_app import celery
from api.models.model import TextContentRequest
from api.services.transformers_service import DEFAULT_NER_MODEL, extract_entities


@celery.task(name="api.ner.extract_entities_task")
def extract_entities_task(content: str):
    result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)
    return result
