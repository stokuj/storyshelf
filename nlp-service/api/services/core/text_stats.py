from __future__ import annotations

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback when optional dep is missing
    tiktoken = None

TOKENIZER_NAME = "cl100k_base"
_TOKENIZER = None


def _get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None and tiktoken is not None:
        _TOKENIZER = tiktoken.get_encoding(TOKENIZER_NAME)
    return _TOKENIZER


def analyse_text(text: str) -> dict:
    """Return analysed text: counts chars, words and tokens."""

    char_count = len(text)
    char_count_clean = sum(ch.isalnum() for ch in text)
    word_count = len(text.split())
    tokenizer = _get_tokenizer()
    if tokenizer is None:
        token_count = len(text) // 4
    else:
        token_count = len(tokenizer.encode(text))

    return {
        "char_count": char_count,
        "char_count_clean": char_count_clean,
        "word_count": word_count,
        "token_count": token_count,
    }
