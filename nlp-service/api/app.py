# app.py

from fastapi import FastAPI

from api.models.model import BookChapter, Book
from api.services.transformers import extract_characters_from_chapter
from api.services.book_service import find_pair_sentences
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

@app.get("/analyse/find_pair_sentences/")
async def get_analyse_find_pair_sentences(book: Book, names: list[str]):
    """
    Funkcja szuka zdań w książce które posiadają 2 podane imiona.
    """

    return find_pair_sentences(book, ["Gandalf", "Bilbo", "Thorin"])

@app.get("/analyse/relations/")
async def get_analyse_relations():
    """
    Otrzymuje liste postaci oraz zdania w których występują.
    Zwraca relacje wykryte dla par postaci.
    """
    return {"message": "This is an example 2"}
