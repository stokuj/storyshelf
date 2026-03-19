import asyncio
import logging

from fastapi import APIRouter, HTTPException
from api.models.model import AcceptedResponse, BookFindPairsPayload
from api.services.find_pairs_service import process_find_pairs


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/books", tags=["find-pairs"])


@router.post("/{bookId}/find-pairs", response_model=AcceptedResponse, status_code=202)
async def find_pairs_endpoint(
    bookId: int | str, payload: BookFindPairsPayload
) -> AcceptedResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")
    if payload.bookId != bookId:
        raise HTTPException(status_code=422, detail="bookId does not match path")

    names = list((payload.characters or {}).keys())
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(
        None, process_find_pairs, payload.content, names, None, bookId
    )

    def _log_result(fut: asyncio.Future) -> None:
        try:
            fut.result()
        except Exception as exc:
            logger.error("Find-pairs executor failed: %s", exc, exc_info=True)

    future.add_done_callback(_log_result)

    return AcceptedResponse(status="accepted")
