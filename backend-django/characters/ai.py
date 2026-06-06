import json
import urllib.error
import urllib.request

from django.conf import settings

HTTP_TIMEOUT = 60
MAX_CHARACTERS = 12


class CharacterGenerationError(Exception):
    """Any failure while generating or parsing the LLM response."""


PROMPT = (
    'For the book "{title}" by {authors}, list the up to {limit} characters most '
    "important to the story. Return STRICT JSON only, no prose, matching exactly:\n"
    '{{"characters": [{{"name": str, "role": short str, "description": one paragraph}}], '
    '"relations": [{{"from": character name, "to": character name, "label": short relation}}]}}\n'
    "Use only character names that appear in the characters list for relations. "
    "If you do not know the book, return empty lists."
)


def _build_prompt(book) -> str:
    authors = ", ".join(book.authors.values_list("name", flat=True)) or "an unknown author"
    return PROMPT.format(title=book.title, authors=authors, limit=MAX_CHARACTERS)


def generate_characters(book) -> dict:
    """Call OpenRouter and return {"characters": [...], "relations": [...]}.

    Raises CharacterGenerationError on any config/HTTP/parse/shape problem.
    """
    if not settings.OPENROUTER_API_KEY:
        raise CharacterGenerationError("OPENROUTER_API_KEY is not configured")

    request_body = json.dumps(
        {
            "model": settings.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": _build_prompt(book)}],
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        settings.OPENROUTER_URL,
        data=request_body,
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # OpenRouter attribution (optional, recommended).
            "HTTP-Referer": "https://github.com/stokuj/storyshelf",
            "X-Title": "StoryShelf",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            envelope = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise CharacterGenerationError(f"OpenRouter request failed: {exc}") from exc

    try:
        content = envelope["choices"][0]["message"]["content"]
        data = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise CharacterGenerationError(f"Malformed OpenRouter response: {exc}") from exc

    if not isinstance(data, dict) or "characters" not in data:
        raise CharacterGenerationError("Response JSON missing 'characters'")
    data.setdefault("relations", [])
    return data
