

from fastapi import APIRouter, HTTPException
from api.models.model import TextContentRequest
from api.services.book_service import analyse_text

router = APIRouter(prefix="/analyse", tags=["analyse"])


@router.post("/")
def analyse_text_endpoint(payload: TextContentRequest):
    if not payload.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty")

    result = analyse_text(payload.content)
    return {"analysis": result}
