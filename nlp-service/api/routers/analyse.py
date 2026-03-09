from fastapi import APIRouter


from api.models.model import TextContentRequest
from api.services.book_service import analyse_text

router = APIRouter(prefix="/analyse", tags=["analyse"])


@router.post("/")
def analyse_text_endpoint(payload: TextContentRequest):
    result = analyse_text(payload.content)
    return {"analysis": result}
