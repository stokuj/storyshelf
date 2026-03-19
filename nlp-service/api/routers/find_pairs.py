from fastapi import APIRouter, HTTPException
from api.models.model import FindPairsResponse, NamesWithContentRequest
from api.services.find_pairs_service import process_find_pairs


router = APIRouter(prefix="/find-pairs", tags=["find-pairs"])


@router.post("/", response_model=FindPairsResponse)
def find_pairs_endpoint(payload: NamesWithContentRequest) -> FindPairsResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    pairs = process_find_pairs(payload.content, payload.names)
    return FindPairsResponse(pairs=pairs)
