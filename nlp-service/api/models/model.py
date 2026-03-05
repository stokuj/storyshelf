# model.py

from pydantic import BaseModel, Field


class Book(BaseModel):
    content: str


class BookChapter(BaseModel):
    number: int
    content: str


class RelationRequest(BaseModel):
    pair: list[str] = Field(min_length=2, max_length=2)
    sentences: list[str] = Field(min_length=1)
