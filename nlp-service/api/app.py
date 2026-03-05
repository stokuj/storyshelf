# app.py

import json
import logging

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db

from api.models.model import BookChapter, RelationRequest
from api.services.transformers import extract_characters_from_chapter
from api.services.book_service import find_pair_sentences
from api.services.llm import LLMService

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
def health():
    """
    Endpoint for health check
    """
    return {"status": "ok", "version": "1.0.0", "timestamp": "2024-01-01T00:00:00Z"}


@app.post("/analyse/")
async def get_analyse(chapter: BookChapter):
    """
    POST /analyse/

    Parameters:
        chapter: BookChapter - obiekt z treścią rozdziału książki

    Returns:
        content: str - treść książki
    """
    return {"content": chapter.content}


@app.post("/analyse/chapter/bert-base-NER")
async def analyse_chapter_bert_base_ner(chapter: BookChapter):
    """
    Analizuje rozdzial i zwraca wykryte postaci,
    uzywajac modelu `dslim/bert-base-NER`.
    """
    return extract_characters_from_chapter(chapter, "dslim/bert-base-NER")


@app.post("/analyse/chapter/bert-large-cased-finetuned-conll03-english")
async def analyse_chapter_bert_large_conll03(chapter: BookChapter):
    """
    Analizuje rozdzial i zwraca wykryte postaci,
    uzywajac modelu `dbmdz/bert-large-cased-finetuned-conll03-english`.
    """
    return extract_characters_from_chapter(
        chapter,
        "dbmdz/bert-large-cased-finetuned-conll03-english",
    )


@app.post("/analyse/find_pair_sentences/")
async def get_analyse_find_pair_sentences(
    book_id: int, names: list[str], db: Session = Depends(get_db)
):
    """
    Funkcja szuka zdań w książce które posiadają liste imion.
    """
    return find_pair_sentences(db, book_id, ["Gandalf", "Bilbo", "Thorin"])


@app.post("/analyse/relations/")
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
