"""LLM service for character relationship extraction."""

from __future__ import annotations

import logging
import os

import openai
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.5-35b-a3b")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))

RELATION_SCHEMA = {
    "family": ["parent_of", "sibling_of", "spouse_of", "ancestor_of"],
    "social": ["friend_of", "enemy_of", "rival_of", "mentor_of", "lover_of", "admires"],
    "hierarchy": ["ruler_of", "commands", "serves", "member_of_faction"],
    "action": ["fights_against", "protects", "betrays", "saves", "hunts"],
    "knowledge": ["knows_secret_of", "manipulates", "deceives"],
    "scifi_fantasy": ["creator_of", "clone_of"],
}

ALL_RELATIONS_STR = "\n".join(
    f"  [{cat}]: {', '.join(rels)}" for cat, rels in RELATION_SCHEMA.items()
)


class LLMService:
    """Extract character relationships from text using an LLM via OpenRouter."""

    def __init__(self, model: str = LLM_MODEL) -> None:
        self._model = model
        self._client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        for marker in ("```", "---", "###", "SYSTEM:", "ASSISTANT:", "USER:"):
            text = text.replace(marker, "")
        return "".join(ch for ch in text if ch == "\n" or ch >= " ")

    def _get_prompt(self, pair: list[str], sentences: list[str]) -> str:
        names_text = ", ".join(self._sanitize(n) for n in pair)
        sentences_text = " ".join(self._sanitize(s) for s in sentences)
        return f"""You are an expert in literary analysis of fantasy and science-fiction.

CHARACTERS: {names_text}

TEXT FRAGMENT: {sentences_text}

TASK:
Extract ONLY relationships directly between {names_text}.
If there is no direct relationship, return empty relations array.

ALLOWED RELATION TYPES (use ONLY these):
{ALL_RELATIONS_STR}

RULES:
- Relations must be supported by the text
- Direction: source → relation → target
- Symmetric relations (friend_of, sibling_of, spouse_of, rival_of) — write once
- evidence must be a direct quote from the text

RETURN ONLY JSON:
{{"relations": [{{"source": "...", "relation": "...", "target": "...", "evidence": "..."}}]}}"""

    def extract_relations(self, pair: list[str], sentences: list[str]) -> str:
        """Extract character relations using LLM."""
        prompt = self._get_prompt(pair, sentences)
        logger.info("Extracting relations for pair: %s", pair)
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=LLM_MAX_TOKENS,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a literary analysis expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                extra_body={"reasoning": {"enabled": False}},
            )
            content = response.choices[0].message.content
            if content is None:
                return '{"relations": []}'
            return content
        except (
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.APIError,
        ) as e:
            logger.error("API error for pair %s: %s", pair, e)
            return '{"relations": []}'


llm_service: LLMService | None = None
if OPENROUTER_API_KEY:
    llm_service = LLMService()
else:
    logger.warning("OPENROUTER_API_KEY not set; LLM features disabled")
