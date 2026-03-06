import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.models.model import BookChapter, RelationRequest, Book
from api.services.book_service import find_pair_sentences
from api.services.llm import LLMService
from api.services.transformers import extract_characters_from_book

router = APIRouter(prefix="/analyse", tags=["analyse"])


@router.post("/")
async def get_analyse(chapter: BookChapter):
    """
    Funkcja testowa, aktualne testuje pipeline danych

    Parameters:
        chapter: BookChapter - obiekt z treścią rozdziału książki

    Returns:
        content: str - treść książki
    """
    return {"content": chapter.content}


@router.post("/book_NER/{book_id}")
async def analyse_book_NER(book_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM books WHERE id = :book_id"),
        {"book_id": book_id},
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")

    book = Book(**row._mapping)

    return extract_characters_from_book(
        book,
        "dbmdz/bert-large-cased-finetuned-conll03-english",
    )


@router.post("/find_pair_sentences/")
async def get_analyse_find_pair_sentences(
    book_id: int, names: list[str], db: Session = Depends(get_db)
):
    """
    Funkcja dla każdej kombinacji names(para):
    - filtruje książke, zwraca te zdania które posiadają daną pare imion.
    """
    return find_pair_sentences(db, book_id, names)


@router.post("/relations/")
async def get_analyse_relations(payload: RelationRequest):
    """
    Funkcja przyjmuje pare postaci i liste zdan,
    a nastepnie wykrywa relacje pomiedzy tymi postaciami.
    """
    llm = LLMService()

    relations_raw = llm.extract_relations(payload.pair, payload.sentences)

    try:
        relations_data = json.loads(relations_raw)
    except (json.JSONDecodeError, TypeError):
        relations_data = {"raw": relations_raw}

    logging.info("Relations for %s: %s", payload.pair, relations_data)
    return {
        "pair": payload.pair,
        "sentences_count": len(payload.sentences),
        "relations": relations_data,
    }
