from fastapi import APIRouter, HTTPException
from api.models.model import AcceptedResponse, ChapterContentPayload
from api.services.analyse_service import process_analyse

router = APIRouter(prefix="/chapters", tags=["analyse"])


@router.post("/{chapterId}/analyse", response_model=AcceptedResponse, status_code=202)
def analyse_text_endpoint(
    chapterId: int | str, payload: ChapterContentPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if payload.chapterId != chapterId:
        raise HTTPException(status_code=422, detail="chapterId does not match path")

    process_analyse(payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
