from __future__ import annotations

from itertools import combinations
import re

SENTENCE_SPLIT_RE = re.compile(
    r"(?:(?<!\bMr\.)(?<!\bMrs\.)(?<!\bMs\.)(?<!\bDr\.)(?<!\bProf\.)"
    r"(?<!\bJr\.)(?<!\bSr\.)(?<!\bSt\.)(?<!\bvs\.))(?<=[.!?])\s+"
)

CHAPTER_HEADER_RE = re.compile(
    r"^\s*(?:Chapter|CHAPTER|Rozdział|ROZDZIAŁ)\s+[IVXLCDM\d]+",
    re.MULTILINE,
)


def find_sentences_with_both_characters(
    content: str, characters: list[str], include_empty: bool = False
) -> list[dict]:
    sentences = [p for p in SENTENCE_SPLIT_RE.split(content.strip()) if p]
    result: list[dict] = []
    for a, b in combinations(characters, 2):
        pa = re.compile(r"\b" + re.escape(a) + r"\b", re.IGNORECASE)
        pb = re.compile(r"\b" + re.escape(b) + r"\b", re.IGNORECASE)
        matching = [s for s in sentences if pa.search(s) and pb.search(s)]
        if include_empty or matching:
            result.append({"pair": [a, b], "sentences": matching})
    return result


def split_into_chapters(text: str) -> list[dict]:
    if not text.strip():
        return []
    parts = CHAPTER_HEADER_RE.split(text)
    headers = CHAPTER_HEADER_RE.findall(text)
    if not headers:
        return [{"number": 1, "title": "", "content": text.strip()}]
    chapters = []
    for i, header in enumerate(headers):
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        chapters.append({"number": i + 1, "title": header.strip(), "content": content})
    return chapters
