"""LLM service for character relationship extraction."""

from __future__ import annotations

import logging
import openai
from openai import AsyncOpenAI, OpenAI
from api.config.settings import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    LLM_MAX_TOKENS,
)

logger = logging.getLogger(__name__)

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
        """Initialise the OpenRouter client.

        Args:
            model: OpenRouter model identifier to use for relation extraction.
        """
        self._model = model
        self._async_client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self._sync_client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        """Strip control characters and prompt-injection markers from user input."""

        # Remove common injection delimiters
        for marker in ("```", "---", "###", "SYSTEM:", "ASSISTANT:", "USER:"):
            text = text.replace(marker, "")
        # Remove ASCII control chars (except newline/space)
        return "".join(ch for ch in text if ch == "\n" or ch >= " ")

    def _get_prompt(self, pair: list[str], sentences: list[str]) -> str:
        names_text = ", ".join(self._sanitize(n) for n in pair)
        sentences_text = " ".join(self._sanitize(s) for s in sentences)

        return f"""You are an expert in literary analysis of fantasy and science-fiction.

        CHARACTERS:
        {names_text}
        
        TEXT FRAGMENT:
        {sentences_text}
        
        TASK:
        Extract all relationships between the characters listed above.
        
        ALLOWED RELATION TYPES (use ONLY these):
        {ALL_RELATIONS_STR}
        
        RULES:
        - Use only relation types from the list above
        - Relations must be supported by the text — either stated directly OR strongly implied by characters' actions and interactions
        - Acceptable inference: characters sharing a meal, traveling together, or one giving orders to another
        - Not acceptable: assuming relationship based on race, species, or role (e.g. "wizard therefore mentor")
        - Direction: source → relation → target (e.g. "Gandalf mentor_of Frodo")
        - Symmetric relations (friend_of, sibling_of, spouse_of, rival_of) — write once
        - Directional relations (betrays, commands, protects, etc.) — source is the one performing the action
        - If the same relation appears multiple times — include it once with the best evidence
        - If no relation exists between two characters — do not invent one
        - evidence must be a direct quote from the text
        
        RETURN ONLY JSON, no text before or after:
        
        {{
          "relations": [
            {{
              "source": "character name",
              "relation": "relation_type",
              "target": "character name",
              "evidence": "direct quote from the text"
            }}
          ]
        }}"""

    async def extract_relations(self, pair: list[str], sentences: list[str]) -> str:
        """Extract relationships between a character pair from the given sentences.

        Args:
            pair: Exactly two character names, e.g. ["Gandalf", "Bilbo"].
            sentences: List of sentences in which both characters appear.

        Returns:
            JSON string with extracted relations:
            {"relations": [{"source": ..., "relation": ..., "target": ..., "evidence": ...}]}
        """
        prompt = self._get_prompt(pair, sentences)

        logger.info("Extracting relations for pair (async): %s", pair)

        try:
            response = await self._async_client.chat.completions.create(
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
                logger.warning("LLM returned None content for pair: %s", pair)
                return '{"relations": []}'
            return content

        except (
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.APIError,
        ) as e:
            logger.error("API error for pair %s: %s", pair, e, exc_info=True)
            return '{"relations": []}'

    def extract_relations_sync(self, pair: list[str], sentences: list[str]) -> str:
        """Synchronous version of extract_relations for Celery workers."""
        prompt = self._get_prompt(pair, sentences)

        logger.info("Extracting relations for pair (sync): %s", pair)

        try:
            response = self._sync_client.chat.completions.create(
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
                logger.warning("LLM returned None content for pair: %s", pair)
                return '{"relations": []}'
            return content

        except (
            openai.RateLimitError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            openai.APIError,
        ) as e:
            logger.error("API error for pair %s: %s", pair, e, exc_info=True)
            return '{"relations": []}'


llm_service = LLMService()
