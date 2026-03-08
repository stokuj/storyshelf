from fastapi import APIRouter, Depends, HTTPException

from api.models.model import TextContentRequest
from api.services.transformers import DEFAULT_NER_MODEL, extract_entities

router = APIRouter(prefix="/ner", tags=["ner"])


# @router.post("/{book_id}")
# def ner_by_id(book_id: int, db: Session = Depends(get_db)):
#     content = get_book_content_by_id(db, book_id)
#     if content is None:
#         raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")
#
#     result = extract_entities(TextContentRequest(content=content), DEFAULT_NER_MODEL)
#     return {"book_id": book_id, "result": result}


@router.post("/")
def ner_by_content(payload: TextContentRequest):
    result = extract_entities(payload, DEFAULT_NER_MODEL)
    return {"result": result}
