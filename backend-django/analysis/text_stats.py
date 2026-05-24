from __future__ import annotations

import logging

try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)
TOKENIZER_NAME = "cl100k_base"
_TOKENIZER = None


def _get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None and tiktoken is not None:
        _TOKENIZER = tiktoken.get_encoding(TOKENIZER_NAME)
    return _TOKENIZER



