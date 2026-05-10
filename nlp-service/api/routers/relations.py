import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request
from api.models.model import AcceptedResponse, BookRelationsPayload
from api.middleware.rate_limiter import limiter
from api.services import process_book_relations_async

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["relations"])


@router.post(
    "/{bookId}/relations",
    summary="Extract character relations",
    description="Uses an LLM to determine the nature of the relationship between two characters based on provided context sentences.",
    response_model=AcceptedResponse,
    status_code=202,
)
@limiter.limit("30/minute")
async def relations(
    request: Request, bookId: int | str, payload: BookRelationsPayload
) -> AcceptedResponse:
    if str(payload.bookId) != str(bookId):
        raise HTTPException(status_code=422, detail="bookId does not match path")

    if not payload.pairs:
        raise HTTPException(status_code=422, detail="pairs list cannot be empty")

    pairs = [pair.model_dump() for pair in payload.pairs]
    task = asyncio.create_task(process_book_relations_async(pairs, bookId))

    def _log_task_result(t: asyncio.Task) -> None:
        try:
            t.result()
        except Exception as exc:
            logger.error("Book relations task failed: %s", exc, exc_info=True)

    task.add_done_callback(_log_task_result)

    return AcceptedResponse(status="accepted")
