from fastapi import APIRouter, HTTPException
from api.models.model import AnalyseResponse, TextContentRequest
from api.services.analyse_service import process_analyse

router = APIRouter(prefix="/analyse", tags=["analyse"])


@router.post("/", response_model=AnalyseResponse)
def analyse_text_endpoint(payload: TextContentRequest) -> AnalyseResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    result = process_analyse(payload.content)
    return AnalyseResponse(analysis=result)
