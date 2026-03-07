# model.py

from pydantic import BaseModel, Field


class Book(BaseModel):
    content: str


class BookChapter(BaseModel):
    number: int
    content: str

class RelationsDirectRequest(BaseModel):
    name_1: str
    name_2: str
    sentences: list[str] = Field(min_length=1)


class BookContentRequest(BaseModel):
    content: str


class NamesRequest(BaseModel):
    names: list[str] = Field(min_length=2)


class NamesWithContentRequest(NamesRequest):
    content: str
