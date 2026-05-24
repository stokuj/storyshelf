from __future__ import annotations

import re
from itertools import combinations

SENTENCE_SPLIT_RE = re.compile(
    r"(?:(?<!\bMr\.)(?<!\bMrs\.)(?<!\bMs\.)(?<!\bDr\.)(?<!\bProf\.)"
    r"(?<!\bJr\.)(?<!\bSr\.)(?<!\bSt\.)(?<!\bvs\.))(?<=[.!?])\s+"
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


