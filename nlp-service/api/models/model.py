from __future__ import annotations

from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, StringConstraints

MAX_CONTENT_LENGTH = 100_000  # ~chapter of a book
MAX_NAME_LENGTH = 100
MAX_SENTENCE_LENGTH = 2_000
MAX_SENTENCES = 500

Name = Annotated[str, StringConstraints(max_length=MAX_NAME_LENGTH)]
Sentence = Annotated[str, StringConstraints(max_length=MAX_SENTENCE_LENGTH)]


class TextContentRequest(BaseModel):
    content: str = Field(max_length=MAX_CONTENT_LENGTH)


class ChapterContentPayload(BaseModel):
    chapterId: int | str
    content: str = Field(max_length=MAX_CONTENT_LENGTH)


class BookFindPairsPayload(BaseModel):
    bookId: int | str
    content: str = Field(max_length=MAX_CONTENT_LENGTH)
    characters: dict[str, int] = Field(default_factory=dict)




class AnalyseStats(BaseModel):
    char_count: int
    char_count_clean: int
    word_count: int
    token_count: int


class AnalyseResponse(BaseModel):
    analysis: AnalyseStats


class AcceptedResponse(BaseModel):
    status: str
    detail: Optional[str] = None


class PairSentences(BaseModel):
    pair: list[Name]
    sentences: list[Sentence]


class BookRelationsPayload(BaseModel):
    bookId: int | str
    pairs: list[PairSentences] = Field(default_factory=list)

