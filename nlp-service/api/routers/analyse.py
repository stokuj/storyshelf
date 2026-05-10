import asyncio

from fastapi import APIRouter, HTTPException
from api.models.model import AcceptedResponse, ChapterContentPayload
from api.services import process_analyse

router = APIRouter(prefix="/chapters", tags=["analyse"])


@router.post(
    "/{chapterId}/analyse",
    summary="Calculate text statistics",
    description="Synchronously calculates character counts, word counts, and token counts for a given chapter content.",
    response_model=AcceptedResponse,
    status_code=202,
)
async def analyse_text_endpoint(
    chapterId: int | str, payload: ChapterContentPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if str(payload.chapterId) != str(chapterId):
        raise HTTPException(status_code=422, detail="chapterId does not match path")

    await asyncio.to_thread(process_analyse, payload.content, chapter_id=chapterId)
    return AcceptedResponse(status="accepted")
