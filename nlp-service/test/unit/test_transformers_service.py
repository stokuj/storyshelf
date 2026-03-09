# tests/test_transformers_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
os.environ["OPENROUTER_API_KEY"] = "fake-key"
from api.services.llm_service import LLMService


#TODO load model:

#TODO is ner model loaded:

#TODO extract entities: