from fastapi import APIRouter

from api.models.model import NamesWithContentRequest
from api.services.book_service import find_sentences_with_both_characters


router = APIRouter(prefix="/find-pairs", tags=["find-pairs"])


@router.post("/")
def find_pairs_endpoint(payload: NamesWithContentRequest):
    pairs = find_sentences_with_both_characters(payload.content, payload.names)
    return {"pairs": pairs}
