from fastapi import APIRouter, HTTPException
from api.models.model import AnalyseResponse, TextContentRequest
from api.services.book_service import analyse_text

router = APIRouter(prefix="/analyse", tags=["analyse"])


@router.post("/", response_model=AnalyseResponse)
def analyse_text_endpoint(payload: TextContentRequest) -> AnalyseResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    result = analyse_text(payload.content)
    return AnalyseResponse(analysis=result)
