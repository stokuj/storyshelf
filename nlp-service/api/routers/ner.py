from fastapi import APIRouter

from api.config.celery_app import celery
from api.models.model import TextContentRequest
from api.services.transformers_service import DEFAULT_NER_MODEL, extract_entities

router = APIRouter(prefix="/ner", tags=["ner"])


@router.post("/", status_code=202)
def ner_by_content(payload: TextContentRequest):
    task = extract_entities_task.delay(payload.content)
    return {"task_id": task.id}


@celery.task(name="api.ner.extract_entities_task")
def extract_entities_task(content: str):
    result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)
    return result


@router.get("/{task_id}")
def extract_entities_status(task_id: str):
    task = celery.AsyncResult(task_id)

    response = {
        "task_id": task.id,
        "state": task.state,
        "ready": task.ready(),
    }

    if task.successful():
        response["result"] = task.result
    elif task.failed():
        response["error"] = str(task.result)

    return response
