#model.py

from pydantic import BaseModel

class Book(BaseModel):
    content: str

class BookChapter(BaseModel):
    number: int
    content: str