"""Book model and loading helpers."""

from __future__ import annotations

import re
from pathlib import Path


class Book:
    def __init__(self, text: str = ""):
        self.text = text

    @property
    def character_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(re.findall(r"\b\w+\b", self.text, flags=re.UNICODE))

    @property
    def sentence_count(self) -> int:
        return len(
            [part for part in re.split(r"(?<=[.!?])\s+", self.text.strip()) if part]
        )

    def stats(self) -> dict[str, int]:
        return {
            "characters": self.character_count,
            "words": self.word_count,
            "sentences": self.sentence_count,
        }

    @classmethod
    def read_txt(cls, file_name: str) -> "Book":
        file_path = Path(file_name)

        with file_path.open("r", encoding="utf-8") as file:
            return cls(file.read())
