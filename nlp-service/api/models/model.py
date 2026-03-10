from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

MAX_CONTENT_LENGTH = 100_000  # ~chapter of a book
MAX_NAME_LENGTH = 100
MAX_SENTENCE_LENGTH = 2_000
MAX_SENTENCES = 500

Name = Annotated[str, StringConstraints(max_length=MAX_NAME_LENGTH)]
Sentence = Annotated[str, StringConstraints(max_length=MAX_SENTENCE_LENGTH)]


class RelationsDirectRequest(BaseModel):
    name_1: Name
    name_2: Name
    sentences: list[Sentence] = Field(min_length=1, max_length=MAX_SENTENCES)


class TextContentRequest(BaseModel):
    content: str = Field(max_length=MAX_CONTENT_LENGTH)


class NamesRequest(BaseModel):
    names: list[Name] = Field(min_length=2)


class NamesWithContentRequest(NamesRequest):
    content: str = Field(max_length=MAX_CONTENT_LENGTH)
