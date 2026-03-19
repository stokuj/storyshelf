from fastapi import APIRouter, HTTPException, Request
from api.models.model import AcceptedResponse, ChapterContentPayload
from api.middleware.rate_limiter import limiter
from api.tasks.ner_task import extract_entities_task

router = APIRouter(prefix="/chapters", tags=["ner"])


@router.post("/{chapterId}/ner", status_code=202, response_model=AcceptedResponse)
@limiter.limit("30/minute")
def ner_by_content(
    request: Request, chapterId: int | str, payload: ChapterContentPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if payload.chapterId != chapterId:
        raise HTTPException(status_code=422, detail="chapterId does not match path")

    extract_entities_task.delay(payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
