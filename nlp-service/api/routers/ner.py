from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.models.model import Book, BookContentRequest
from api.services.book_service import get_book_content_by_id
from api.services.transformers import DEFAULT_NER_MODEL, extract_characters_from_book

router = APIRouter(prefix="/ner", tags=["ner"])


@router.post("/{book_id}")
async def ner_by_id(book_id: int, db: Session = Depends(get_db)):
    content = get_book_content_by_id(db, book_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")

    result = extract_characters_from_book(Book(content=content), DEFAULT_NER_MODEL)
    return {"book_id": book_id, "result": result}


@router.post("/")
async def ner_by_content(payload: BookContentRequest):
    result = extract_characters_from_book(
        Book(content=payload.content), DEFAULT_NER_MODEL
    )
    return {"result": result}
