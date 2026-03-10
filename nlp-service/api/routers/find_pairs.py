

from fastapi import APIRouter, HTTPException
from api.models.model import NamesWithContentRequest
from api.services.book_service import find_sentences_with_both_characters


router = APIRouter(prefix="/find-pairs", tags=["find-pairs"])


@router.post("/")
def find_pairs_endpoint(payload: NamesWithContentRequest):
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    if not payload.names:
        raise HTTPException(status_code=422, detail="Names cannot be empty")

    pairs = find_sentences_with_both_characters(payload.content, payload.names)
    return {"pairs": pairs}
