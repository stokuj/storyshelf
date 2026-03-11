from fastapi import APIRouter, HTTPException, Request
from api.config.celery_app import celery
from api.models.model import TextContentRequest
from api.middleware.rate_limiter import limiter
from api.tasks.ner_task import extract_entities_task

router = APIRouter(prefix="/ner", tags=["ner"])


@router.post("/", status_code=202)
@limiter.limit("5/minute")
def ner_by_content(request: Request, payload: TextContentRequest):
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    task = extract_entities_task.delay(payload.content)
    return {"task_id": task.id}


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
