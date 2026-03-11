from typing import Annotated, Any, Optional

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


class AnalyseStats(BaseModel):
    char_count: int
    char_count_clean: int
    word_count: int
    token_count: int


class AnalyseResponse(BaseModel):
    analysis: AnalyseStats


class TaskAcceptedResponse(BaseModel):
    task_id: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    ready: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class RelationsResponse(BaseModel):
    pair: list[Name]
    sentences_count: int
    relations: Any


class PairSentences(BaseModel):
    pair: list[Name]
    sentences: list[Sentence]


class FindPairsResponse(BaseModel):
    pairs: list[PairSentences]
