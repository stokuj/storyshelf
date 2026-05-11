# Target Architecture Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove NLP HTTP service. Port NER/LLM engines directly into Django Celery workers with queue routing, DLX, Flower, and the new entity model (BookCharacter/BookPlace/BookOrganization/CharacterRelationship).

**Architecture:** Two Celery worker pools: `celery-ner` (prefork, CPU-bound BERT) and `celery-llm` (gevent, I/O-bound OpenRouter). Admin uploads book text, system splits into chapters, each chapter analyzed async. Results stored temporarily as `Chapter.ner_pending` JSON. After all chapters complete, `merge_book_ner` upserts entities into global tables and clears chapter text. LLM extracts CharacterRelationship entries.

**Tech Stack:** Django 6, Celery 5.6, PyTorch 2.10, HuggingFace Transformers, OpenAI, RabbitMQ 3, Redis 7, Flower

---

## Entity Model (final)

```
BookCharacter         (id, name UNIQUE, description NULL, mention_count DEFAULT 0)
BookPlace             (id, name UNIQUE, description NULL, mention_count DEFAULT 0)
BookOrganization      (id, name UNIQUE, description NULL, mention_count DEFAULT 0)

CharacterRelationship (id, from_character FK→BookCharacter, to_character FK→BookCharacter,
                       relation_type VARCHAR(30), book FK→Book,
                       UNIQUE(from_character, to_character, book))

Book                  (id, title, description, cover, avg_rating, ..., ner_completed_count)
  → Chapter           (id, book FK, chapter_number, title, text, ner_pending JSON NULL,
                       analysis_completed, char_count, word_count, token_count ...)
```

No junction tables. Per-chapter NER results are temporary JSON in `Chapter.ner_pending`, cleared after merge.
Characters-for-book query: since no junction table exists, the frontend/serializer queries global BookCharacter entities. CharacterRelationship has `book` FK for scoping relations per book.

---

## File Map

**Create:**
- `backend-django/analysis/ner_engine.py`
- `backend-django/analysis/llm_engine.py`
- `backend-django/analysis/text_parser.py`
- `backend-django/analysis/text_stats.py`
- `backend-django/analysis/models.py`
- `backend-django/analysis/admin.py`
- `backend-django/analysis/tests/conftest.py`
- `backend-django/analysis/tests/test_ner_engine.py`
- `backend-django/analysis/tests/test_llm_engine.py`
- `backend-django/analysis/tests/test_text_parser.py`
- `backend-django/analysis/tests/test_text_stats.py`
- `backend-django/analysis/tests/test_models.py`
- `backend-django/analysis/tests/test_tasks.py`
- `backend-django/reviews/signals.py`
- `infra/rabbitmq/definitions.json`

**Modify:**
- `backend-django/pyproject.toml` — add torch, transformers, openai, tiktoken, flower, gevent
- `backend-django/config/settings/base.py` — CELERY_TASK_ROUTES, remove NLP_SERVICE_URL, remove InternalEndpointMiddleware
- `backend-django/config/urls.py` — remove `api/internal/` route
- `backend-django/analysis/tasks.py` — rewrite all tasks
- `backend-django/analysis/apps.py` — no change needed (signals in reviews app)
- `backend-django/books/models.py` — remove StoryCharacter, old BookCharacter, old CharacterRelation; add ner_pending to Chapter; rename rating→avg_rating
- `backend-django/books/views.py` — remove auto-trigger (ner_chapter.delay), update entity references
- `backend-django/books/serializers.py` — update to new entity models
- `backend-django/books/urls.py` — update character/relation view paths
- `backend-django/reviews/models.py` — add avg_rating signal import
- `backend-django/reviews/apps.py` — register signal
- `backend-django/shelf/models.py` — add start_date, finish_date, personal_rating
- `infra/compose/docker-compose.dev.yml` — split worker, add flower, remove nlp-service, RabbitMQ definitions mount
- `infra/compose/docker-compose.prod.yml` — same + fix RabbitMQ v4→v3

**Delete:**
- `nlp-service/` (entire directory)
- `backend-django/analysis/callbacks.py`
- `backend-django/analysis/urls.py`
- `backend-django/analysis/middleware.py`
- `backend-django/analysis/tests/test_views.py`

---

### Task 1: Remove NLP service and dead code

**Files:**
- Delete: `nlp-service/` (entire directory)
- Delete: `backend-django/analysis/callbacks.py`
- Delete: `backend-django/analysis/urls.py`
- Delete: `backend-django/analysis/middleware.py`
- Delete: `backend-django/analysis/tests/test_views.py`
- Modify: `backend-django/config/urls.py` — remove line `path("api/internal/", include("analysis.urls")),`
- Modify: `backend-django/config/settings/base.py` — remove `InternalEndpointMiddleware` from MIDDLEWARE (line 42)
- Modify: `backend-django/config/settings/base.py` — remove `NLP_SERVICE_URL` (line 116)

- [ ] **Step 1: Delete files and directories**

```bash
rm -rf nlp-service/
rm backend-django/analysis/callbacks.py
rm backend-django/analysis/urls.py
rm backend-django/analysis/middleware.py
rm backend-django/analysis/tests/test_views.py
```

- [ ] **Step 2: Remove internal endpoints from URL config**

In `backend-django/config/urls.py`, remove the line:
```python
path("api/internal/", include("analysis.urls")),
```

- [ ] **Step 3: Remove InternalEndpointMiddleware and NLP_SERVICE_URL from settings**

In `backend-django/config/settings/base.py`, remove from MIDDLEWARE list:
```python
"analysis.middleware.InternalEndpointMiddleware",
```

And remove the line:
```python
NLP_SERVICE_URL = os.getenv("NLP_SERVICE_URL", "http://nlp-service:8000")
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove NLP service, internal endpoints, and dead middleware"
```

---

### Task 2: Add dependencies

**Files:**
- Modify: `backend-django/pyproject.toml`

- [ ] **Step 1: Add dependencies to pyproject.toml**

Add to the `dependencies` list:
```toml
"torch>=2.10",
"transformers>=4.57",
"openai>=1.0",
"tiktoken>=0.7",
"gevent>=24",
"flower>=2.0",
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend-django && uv sync
```

- [ ] **Step 3: Commit**

```bash
git add backend-django/pyproject.toml backend-django/uv.lock
git commit -m "chore: add torch, transformers, openai, tiktoken, gevent, flower"
```

---

### Task 3: Port NER engine

**Files:**
- Create: `backend-django/analysis/ner_engine.py`
- Create: `backend-django/analysis/tests/test_ner_engine.py`

- [ ] **Step 1: Write failing test**

Write `backend-django/analysis/tests/test_ner_engine.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


class TestLoadNerModel:
    def test_load_with_mock_pipeline(self):
        with patch("analysis.ner_engine.pipeline") as mock_pipeline:
            from analysis.ner_engine import load_ner_model
            result = load_ner_model("test-model")
            assert result is True

    def test_load_returns_false_on_error(self):
        with patch("analysis.ner_engine.pipeline", side_effect=OSError("no model")):
            from analysis.ner_engine import load_ner_model
            result = load_ner_model("missing-model")
            assert result is False


class TestExtractEntities:
    def test_groups_by_entity_type(self):
        fake_pipeline = MagicMock()
        fake_pipeline.return_value = [
            {"word": "Frodo", "entity_group": "PER"},
            {"word": "Frodo", "entity_group": "PER"},
            {"word": "Gandalf", "entity_group": "PER"},
            {"word": "Shire", "entity_group": "LOC"},
            {"word": "Fellowship", "entity_group": "ORG"},
        ]
        with patch("analysis.ner_engine.load_ner_model", return_value=True):
            with patch("analysis.ner_engine._NER_PIPELINES", {"test-model": fake_pipeline}):
                from analysis.ner_engine import extract_entities
                result = extract_entities("text", model="test-model")
        assert result["characters"] == {"Frodo": 2, "Gandalf": 1}
        assert result["locations"] == {"Shire": 1}
        assert result["organizations"] == {"Fellowship": 1}
        assert result["miscellaneous"] == {}

    def test_misc_always_empty(self):
        fake_pipeline = MagicMock()
        fake_pipeline.return_value = [
            {"word": "Sword", "entity_group": "MISC"},
        ]
        with patch("analysis.ner_engine.load_ner_model", return_value=True):
            with patch("analysis.ner_engine._NER_PIPELINES", {"test-model": fake_pipeline}):
                from analysis.ner_engine import extract_entities
                result = extract_entities("text", model="test-model")
        assert result["miscellaneous"] == {}

    def test_returns_empty_on_failed_load(self):
        with patch("analysis.ner_engine.load_ner_model", return_value=False):
            from analysis.ner_engine import extract_entities
            result = extract_entities("text")
        assert result == {}
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_ner_engine.py -v
```

- [ ] **Step 3: Write ner_engine.py**

```python
# backend-django/analysis/ner_engine.py
from __future__ import annotations

from collections import Counter
import logging
import os
import time
from typing import Any, Callable, cast

from transformers import pipeline

logger = logging.getLogger(__name__)
DEFAULT_NER_MODEL = os.getenv(
    "NER_MODEL", "dbmdz/bert-large-cased-finetuned-conll03-english"
)
NER_MIN_OCCURRENCES = int(os.getenv("NER_MIN_OCCURRENCES", "5"))
_NER_PIPELINES: dict[str, Any] = {}


def load_ner_model(model: str) -> bool:
    if model in _NER_PIPELINES:
        return True
    try:
        logger.info("Loading NER model: %s (pid=%s)", model, os.getpid())
        _NER_PIPELINES[model] = pipeline(
            task="token-classification",
            model=model,
            aggregation_strategy="first",
            stride=128,
        )
        logger.info("NER model loaded: %s", model)
        return True
    except (OSError, EnvironmentError) as exc:
        logger.warning("Model '%s' unavailable: %s", model, exc)
        return False


def extract_entities(text: str, model: str = DEFAULT_NER_MODEL) -> dict:
    """Extract named entities from text.

    Returns dict: {characters, organizations, locations, miscellaneous}.
    Each value is {name: count} sorted by count descending.
    MISC is always empty dict — ignored per project spec.
    """
    if not load_ner_model(model):
        return {}

    ner = cast(Callable[[str], list[dict]], _NER_PIPELINES[model])
    start_time = time.perf_counter()
    entities = ner(text)

    group_map: dict[str, list[str]] = {
        "characters": [], "organizations": [], "locations": [], "miscellaneous": [],
    }
    group_to_key = {
        "PER": "characters", "PERSON": "characters",
        "ORG": "organizations", "LOC": "locations", "MISC": "miscellaneous",
    }

    for entity in entities:
        word = entity.get("word", "").strip()
        group = entity.get("entity_group")
        if group is not None:
            key = group_to_key.get(str(group))
            if word and key:
                group_map[key].append(word)

    def sorted_counts(names: list[str], min_occ: int = 1) -> dict[str, int]:
        counts = Counter(names)
        filtered = {n: c for n, c in counts.items() if c >= min_occ}
        return dict(sorted(filtered.items(), key=lambda x: x[1], reverse=True))

    elapsed = time.perf_counter() - start_time
    logger.info("NER execution: %.3f s", elapsed)

    return {
        "engine": "transformers",
        "model_name": model,
        "characters": sorted_counts(group_map["characters"], NER_MIN_OCCURRENCES),
        "organizations": sorted_counts(group_map["organizations"], NER_MIN_OCCURRENCES),
        "locations": sorted_counts(group_map["locations"], NER_MIN_OCCURRENCES),
        "miscellaneous": {},
        "execution_time_seconds": round(elapsed, 3),
    }
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_ner_engine.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/analysis/ner_engine.py backend-django/analysis/tests/test_ner_engine.py
git commit -m "feat: port NER engine to Django analysis app"
```

---

### Task 4: Port text stats and text parser

**Files:**
- Create: `backend-django/analysis/text_stats.py`
- Create: `backend-django/analysis/text_parser.py`
- Create: `backend-django/analysis/tests/test_text_stats.py`
- Create: `backend-django/analysis/tests/test_text_parser.py`

- [ ] **Step 1: Write failing test for text_stats.py**

Write `backend-django/analysis/tests/test_text_stats.py`:

```python
import pytest


class TestAnalyseText:
    def test_basic_counts(self):
        from analysis.text_stats import analyse_text
        result = analyse_text("Hello world")
        assert result["char_count"] == 11
        assert result["char_count_clean"] == 10
        assert result["word_count"] == 2
        assert result["token_count"] > 0

    def test_empty_string(self):
        from analysis.text_stats import analyse_text
        result = analyse_text("")
        assert result["char_count"] == 0
        assert result["word_count"] == 0

    def test_whitespace_only(self):
        from analysis.text_stats import analyse_text
        result = analyse_text("   \n  \t  ")
        assert result["word_count"] == 0
        assert result["char_count_clean"] == 0
```

- [ ] **Step 2: Write failing test for text_parser.py**

Write `backend-django/analysis/tests/test_text_parser.py`:

```python
import pytest


class TestFindSentencesWithBothCharacters:
    def test_finds_sentences_with_both(self):
        from analysis.text_parser import find_sentences_with_both_characters
        text = "Frodo walked to Mordor. Sam followed Frodo. Gandalf elsewhere."
        result = find_sentences_with_both_characters(text, ["Frodo", "Sam", "Gandalf"])
        pairs_found = {tuple(r["pair"]) for r in result}
        assert ("Frodo", "Sam") in pairs_found

    def test_case_insensitive(self):
        from analysis.text_parser import find_sentences_with_both_characters
        text = "FRODO and sam walked."
        result = find_sentences_with_both_characters(text, ["Frodo", "Sam"])
        assert len(result) == 1

    def test_word_boundary(self):
        from analysis.text_parser import find_sentences_with_both_characters
        text = "Bilbo and Baggins."
        result = find_sentences_with_both_characters(text, ["Bilbo", "Bag"])
        assert len(result) == 0

    def test_single_character_returns_empty(self):
        from analysis.text_parser import find_sentences_with_both_characters
        result = find_sentences_with_both_characters("Frodo walked.", ["Frodo"])
        assert len(result) == 0


class TestSplitIntoChapters:
    def test_english_headers(self):
        from analysis.text_parser import split_into_chapters
        text = "Chapter 1\nFrodo walked.\nChapter 2\nSam followed."
        result = split_into_chapters(text)
        assert len(result) == 2
        assert result[0]["title"] == "Chapter 1"
        assert result[0]["number"] == 1

    def test_polish_headers(self):
        from analysis.text_parser import split_into_chapters
        text = "Rozdział 1\nPoczątek.\nRozdział 2\nŚrodek."
        result = split_into_chapters(text)
        assert len(result) == 2

    def test_no_headers_returns_one_chapter(self):
        from analysis.text_parser import split_into_chapters
        text = "Just some text."
        result = split_into_chapters(text)
        assert len(result) == 1
        assert result[0]["number"] == 1

    def test_empty_text(self):
        from analysis.text_parser import split_into_chapters
        assert split_into_chapters("") == []
```

- [ ] **Step 3: Run tests — expect FAIL**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_text_stats.py analysis/tests/test_text_parser.py -v
```

- [ ] **Step 4: Write text_stats.py**

```python
# backend-django/analysis/text_stats.py
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


def analyse_text(text: str) -> dict:
    char_count = len(text)
    char_count_clean = sum(ch.isalnum() for ch in text)
    word_count = len(text.split())
    tokenizer = _get_tokenizer()
    if tokenizer is None:
        logger.warning("tiktoken unavailable, using fallback")
        token_count = len(text) // 4
    else:
        token_count = len(tokenizer.encode(text))
    return {
        "char_count": char_count,
        "char_count_clean": char_count_clean,
        "word_count": word_count,
        "token_count": token_count,
    }
```

- [ ] **Step 5: Write text_parser.py**

```python
# backend-django/analysis/text_parser.py
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
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_text_stats.py analysis/tests/test_text_parser.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend-django/analysis/text_stats.py backend-django/analysis/text_parser.py \
        backend-django/analysis/tests/test_text_stats.py backend-django/analysis/tests/test_text_parser.py
git commit -m "feat: port text stats and text parser from NLP service"
```

---

### Task 5: Create entity models

**Files:**
- Create: `backend-django/analysis/models.py`
- Modify: `backend-django/books/models.py` — remove old models, add ner_pending, rename rating→avg_rating
- Modify: `backend-django/shelf/models.py` — add start_date, finish_date, personal_rating
- Create: `backend-django/analysis/tests/conftest.py`
- Create: `backend-django/analysis/tests/test_models.py`

- [ ] **Step 1: Write analysis/models.py**

```python
# backend-django/analysis/models.py
from django.db import models


class BookCharacter(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class BookPlace(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class BookOrganization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class CharacterRelationship(models.Model):
    class RelationType(models.TextChoices):
        PARENT_OF = "parent_of"
        SIBLING_OF = "sibling_of"
        SPOUSE_OF = "spouse_of"
        ANCESTOR_OF = "ancestor_of"
        FRIEND_OF = "friend_of"
        ENEMY_OF = "enemy_of"
        RIVAL_OF = "rival_of"
        MENTOR_OF = "mentor_of"
        LOVER_OF = "lover_of"
        ADMIRES = "admires"
        RULER_OF = "ruler_of"
        COMMANDS = "commands"
        SERVES = "serves"
        MEMBER_OF_FACTION = "member_of_faction"
        FIGHTS_AGAINST = "fights_against"
        PROTECTS = "protects"
        BETRAYS = "betrays"
        SAVES = "saves"
        HUNTS = "hunts"
        KNOWS_SECRET_OF = "knows_secret_of"
        MANIPULATES = "manipulates"
        DECEIVES = "deceives"
        CREATOR_OF = "creator_of"
        CLONE_OF = "clone_of"

    from_character = models.ForeignKey(
        BookCharacter, on_delete=models.CASCADE, related_name="relations_from"
    )
    to_character = models.ForeignKey(
        BookCharacter, on_delete=models.CASCADE, related_name="relations_to"
    )
    relation_type = models.CharField(max_length=30, choices=RelationType.choices)
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="character_relationships"
    )

    class Meta:
        unique_together = ("from_character", "to_character", "book")

    def __str__(self):
        return f"{self.from_character.name} {self.relation_type} {self.to_character.name}"
```

- [ ] **Step 2: Rewrite books/models.py**

Replace entire file:

```python
# backend-django/books/models.py
from django.db import models


class Chapter(models.Model):
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name="chapters")
    chapter_number = models.IntegerField()
    title = models.CharField(max_length=150, blank=True, default="")
    text = models.TextField()
    analysis_completed = models.BooleanField(default=False)
    char_count = models.IntegerField(null=True, blank=True)
    char_count_clean = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    token_count = models.IntegerField(null=True, blank=True)
    ner_pending = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("chapter_number",)


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="books",
    )
    title = models.CharField(max_length=500, blank=True, default="")
    year = models.IntegerField(default=0)
    isbn = models.CharField(max_length=20, blank=True, default="")
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=0)
    position_in_series = models.IntegerField(null=True, blank=True)
    chapters_count = models.IntegerField(default=0)
    ner_completed_count = models.IntegerField(default=0)
    avg_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.JSONField(default=list)


class BookAuthor(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    author = models.ForeignKey("library.Author", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        unique_together = ("book", "author")


class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey("library.Tag", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("book", "tag")
```

Key changes from old model:
- Removed `StoryCharacter`, `BookCharacter` (old M2M), `CharacterRelation` (old)
- `content` → `text` on Chapter
- Removed `ner_result`, added `ner_pending` (temporary JSON during processing)
- `rating` → `avg_rating` on Book

- [ ] **Step 3: Modify shelf/models.py**

Add to imports:
```python
from django.core.validators import MaxValueValidator, MinValueValidator
```

Add to `ShelfEntry` fields (after `status`):
```python
start_date = models.DateField(null=True, blank=True)
finish_date = models.DateField(null=True, blank=True)
personal_rating = models.IntegerField(
    null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
)
```

- [ ] **Step 4: Write conftest.py for tests**

```python
# backend-django/analysis/tests/conftest.py
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def book(db):
    from books.models import Book
    return Book.objects.create(title="Test Book")


@pytest.fixture
def character_a(db):
    from analysis.models import BookCharacter
    return BookCharacter.objects.create(name="Frodo")


@pytest.fixture
def character_b(db):
    from analysis.models import BookCharacter
    return BookCharacter.objects.create(name="Sam")
```

- [ ] **Step 5: Write model tests**

```python
# backend-django/analysis/tests/test_models.py
import pytest
from django.db import IntegrityError


class TestBookCharacter:
    def test_create(self, django_db_setup):
        from analysis.models import BookCharacter
        c = BookCharacter.objects.create(name="Frodo", mention_count=5)
        assert c.name == "Frodo"
        assert c.mention_count == 5
        assert c.description is None

    def test_name_unique(self, django_db_setup):
        from analysis.models import BookCharacter
        BookCharacter.objects.create(name="Gandalf")
        with pytest.raises(IntegrityError):
            BookCharacter.objects.create(name="Gandalf")

    def test_mention_count_default(self, django_db_setup):
        from analysis.models import BookCharacter
        c = BookCharacter.objects.create(name="Sam")
        assert c.mention_count == 0


class TestCharacterRelationship:
    def test_create(self, django_db_setup, book, character_a, character_b):
        from analysis.models import CharacterRelationship
        r = CharacterRelationship.objects.create(
            from_character=character_a, to_character=character_b,
            relation_type="friend_of", book=book,
        )
        assert r.relation_type == "friend_of"

    def test_unique_together(self, django_db_setup, book, character_a, character_b):
        from analysis.models import CharacterRelationship
        CharacterRelationship.objects.create(
            from_character=character_a, to_character=character_b,
            relation_type="friend_of", book=book,
        )
        with pytest.raises(IntegrityError):
            CharacterRelationship.objects.create(
                from_character=character_a, to_character=character_b,
                relation_type="enemy_of", book=book,
            )


class TestChapterNerPending:
    def test_ner_pending_nullable(self, django_db_setup, book):
        from books.models import Chapter
        c = Chapter.objects.create(book=book, chapter_number=1, text="test")
        assert c.ner_pending is None

    def test_ner_pending_stores_json(self, django_db_setup, book):
        from books.models import Chapter
        c = Chapter.objects.create(
            book=book, chapter_number=1, text="t",
            ner_pending={"characters": {"Frodo": 1}},
        )
        assert c.ner_pending == {"characters": {"Frodo": 1}}
```

- [ ] **Step 6: Generate migrations and run tests**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations
cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate
cd backend-django && DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb uv run python -m pytest analysis/tests/test_models.py -v
```

Expected: PASS (7 tests)

- [ ] **Step 7: Commit**

```bash
git add backend-django/analysis/models.py backend-django/books/models.py \
        backend-django/shelf/models.py backend-django/analysis/tests/conftest.py \
        backend-django/analysis/tests/test_models.py \
        backend-django/analysis/migrations/ backend-django/books/migrations/ \
        backend-django/shelf/migrations/
git commit -m "feat: create entity models and update Book/Chapter/ShelfEntry"
```

---

### Task 6: Port LLM engine

**Files:**
- Create: `backend-django/analysis/llm_engine.py`
- Create: `backend-django/analysis/tests/test_llm_engine.py`

- [ ] **Step 1: Write test**

```python
# backend-django/analysis/tests/test_llm_engine.py
import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestExtractRelations:
    @pytest.fixture(autouse=True)
    def setup_env(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-key"

    def test_extract_relations_sync(self):
        mock_resp = MagicMock()
        mock_resp.choices = [
            MagicMock(message=MagicMock(
                content=json.dumps({"relations": [
                    {"source": "Frodo", "relation": "friend_of",
                     "target": "Sam", "evidence": "walked"}
                ]})
            ))
        ]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService
            svc = LLMService(model="test")
            result = svc.extract_relations_sync(["Frodo", "Sam"], ["walked together"])
        parsed = json.loads(result)
        assert len(parsed["relations"]) == 1

    def test_returns_empty_on_none_content(self):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_resp

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService
            svc = LLMService(model="test")
            result = svc.extract_relations_sync(["A", "B"], ["t"])
        assert result == '{"relations": []}'

    def test_returns_empty_on_api_error(self):
        import openai
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError("t/o")

        with patch("analysis.llm_engine.OpenAI", return_value=mock_client):
            from analysis.llm_engine import LLMService
            svc = LLMService(model="test")
            result = svc.extract_relations_sync(["A", "B"], ["t"])
        assert result == '{"relations": []}'

    def test_sanitize_removes_injection(self):
        from analysis.llm_engine import LLMService
        result = LLMService._sanitize("SYSTEM: hello\n```code```")
        assert "SYSTEM:" not in result
        assert "```" not in result
        assert "hello" in result
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd backend-django && DJANGO_ENV=dev OPENROUTER_API_KEY=fake-key uv run python -m pytest analysis/tests/test_llm_engine.py -v
```

- [ ] **Step 3: Write llm_engine.py**

```python
# backend-django/analysis/llm_engine.py
"""LLM service for character relationship extraction."""

from __future__ import annotations

import logging
import os
import openai
from openai import AsyncOpenAI, OpenAI

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
        self._async_client = AsyncOpenAI(
            base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY,
        )
        self._sync_client = OpenAI(
            base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY,
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

    async def extract_relations(self, pair: list[str], sentences: list[str]) -> str:
        prompt = self._get_prompt(pair, sentences)
        logger.info("Extracting relations for pair (async): %s", pair)
        try:
            response = await self._async_client.chat.completions.create(
                model=self._model, max_tokens=LLM_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                extra_body={"reasoning": {"enabled": False}},
            )
            content = response.choices[0].message.content
            if content is None:
                logger.warning("LLM returned None for pair: %s", pair)
                return '{"relations": []}'
            return content
        except (openai.RateLimitError, openai.APITimeoutError,
                openai.APIConnectionError, openai.APIError) as e:
            logger.error("API error for pair %s: %s", pair, e)
            return '{"relations": []}'

    def extract_relations_sync(self, pair: list[str], sentences: list[str]) -> str:
        """Synchronous version for Celery workers."""
        prompt = self._get_prompt(pair, sentences)
        logger.info("Extracting relations for pair (sync): %s", pair)
        try:
            response = self._sync_client.chat.completions.create(
                model=self._model, max_tokens=LLM_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": "You are a literary analysis expert. Return only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                extra_body={"reasoning": {"enabled": False}},
            )
            content = response.choices[0].message.content
            if content is None:
                return '{"relations": []}'
            return content
        except (openai.RateLimitError, openai.APITimeoutError,
                openai.APIConnectionError, openai.APIError) as e:
            logger.error("API error for pair %s: %s", pair, e)
            return '{"relations": []}'


llm_service = LLMService()
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev OPENROUTER_API_KEY=fake-key uv run python -m pytest analysis/tests/test_llm_engine.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/analysis/llm_engine.py backend-django/analysis/tests/test_llm_engine.py
git commit -m "feat: port LLM engine from NLP service"
```

---

### Task 7: Rewrite Celery tasks

**Files:**
- Modify: `backend-django/analysis/tasks.py` — full rewrite
- Create: `backend-django/analysis/tests/test_tasks.py`

- [ ] **Step 1: Write task tests**

```python
# backend-django/analysis/tests/test_tasks.py
import pytest
from unittest.mock import patch


class TestAnalyseChapter:
    def test_updates_chapter_stats(self, db, book):
        from books.models import Chapter
        chapter = Chapter.objects.create(book=book, chapter_number=1, text="Hello world test")
        from analysis.tasks import analyse_chapter
        analyse_chapter(chapter.id, "Hello world test")
        chapter.refresh_from_db()
        assert chapter.analysis_completed is True
        assert chapter.word_count == 3
        assert chapter.char_count > 0

    def test_skips_if_already_completed(self, db, book):
        from books.models import Chapter
        chapter = Chapter.objects.create(
            book=book, chapter_number=1, text="test",
            analysis_completed=True, char_count=4, word_count=1, token_count=2,
        )
        from analysis.tasks import analyse_chapter
        analyse_chapter(chapter.id, "test")
        chapter.refresh_from_db()
        assert chapter.char_count == 4


class TestNerChapter:
    def test_stores_ner_pending(self, db, book):
        from books.models import Chapter
        chapter = Chapter.objects.create(book=book, chapter_number=1, text="Frodo")
        book.chapters_count = 1
        book.save()

        with patch("analysis.tasks.extract_entities") as mock_ner:
            mock_ner.return_value = {"characters": {"Frodo": 2}, "organizations": {}, "locations": {}}
            from analysis.tasks import ner_chapter
            ner_chapter(chapter.id, "Frodo")

        chapter.refresh_from_db()
        assert chapter.ner_pending["characters"] == {"Frodo": 2}

    def test_skips_if_already_processed(self, db, book):
        from books.models import Chapter
        chapter = Chapter.objects.create(
            book=book, chapter_number=1, text="test",
            ner_pending={"characters": {"Frodo": 1}},
        )
        with patch("analysis.tasks.extract_entities") as mock_ner:
            from analysis.tasks import ner_chapter
            ner_chapter(chapter.id, "test")
            mock_ner.assert_not_called()

    def test_triggers_merge_when_all_done(self, db, book):
        from books.models import Chapter
        chapter = Chapter.objects.create(book=book, chapter_number=1, text="Frodo")
        book.chapters_count = 1
        book.save()

        with patch("analysis.tasks.extract_entities") as mock_ner:
            with patch("analysis.tasks.merge_book_ner.delay") as mock_merge:
                mock_ner.return_value = {"characters": {"Frodo": 1}, "organizations": {}, "locations": {}}
                from analysis.tasks import ner_chapter
                ner_chapter(chapter.id, "Frodo")
            mock_merge.assert_called_once_with(book.id)


class TestMergeBookNer:
    def test_upserts_entities(self, db, book):
        from books.models import Chapter
        from analysis.models import BookCharacter, BookPlace
        Chapter.objects.create(
            book=book, chapter_number=1, text="old",
            ner_pending={"characters": {"Frodo": 2}, "locations": {"Shire": 3}},
        )
        Chapter.objects.create(
            book=book, chapter_number=2, text="old",
            ner_pending={"characters": {"Frodo": 1, "Gandalf": 2}},
        )

        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner
            merge_book_ner(book.id)

        frodo = BookCharacter.objects.get(name="Frodo")
        assert frodo.mention_count == 3
        gandalf = BookCharacter.objects.get(name="Gandalf")
        assert gandalf.mention_count == 2
        shire = BookPlace.objects.get(name="Shire")
        assert shire.mention_count == 3

    def test_clears_chapter_text(self, db, book):
        from books.models import Chapter
        ch = Chapter.objects.create(
            book=book, chapter_number=1, text="Frodo walked",
            ner_pending={"characters": {"Frodo": 1}},
        )
        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner
            merge_book_ner(book.id)
        ch.refresh_from_db()
        assert ch.text == ""
        assert ch.ner_pending is None

    def test_increments_existing_mention_count(self, db, book):
        from books.models import Chapter
        from analysis.models import BookCharacter
        BookCharacter.objects.create(name="Frodo", mention_count=5)
        ch = Chapter.objects.create(
            book=book, chapter_number=1, text="old",
            ner_pending={"characters": {"Frodo": 2}},
        )
        with patch("analysis.tasks.find_pairs.delay"):
            from analysis.tasks import merge_book_ner
            merge_book_ner(book.id)
        frodo = BookCharacter.objects.get(name="Frodo")
        assert frodo.mention_count == 7
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb uv run python -m pytest analysis/tests/test_tasks.py -v
```

- [ ] **Step 3: Write tasks.py**

```python
# backend-django/analysis/tasks.py
from celery import shared_task
from django.db import transaction
from django.db.models import F


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyse_chapter(self, chapter_id: int, content: str):
    from books.models import Chapter
    from .text_stats import analyse_text

    chapter = Chapter.objects.get(id=chapter_id)
    if chapter.analysis_completed:
        return

    stats = analyse_text(content)
    chapter.char_count = stats["char_count"]
    chapter.char_count_clean = stats["char_count_clean"]
    chapter.word_count = stats["word_count"]
    chapter.token_count = stats["token_count"]
    chapter.analysis_completed = True
    chapter.save()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def ner_chapter(self, chapter_id: int, content: str):
    from books.models import Book, Chapter
    from .ner_engine import extract_entities

    chapter = Chapter.objects.select_related("book").get(id=chapter_id)
    if chapter.ner_pending is not None:
        return

    result = extract_entities(content)
    chapter.ner_pending = result
    chapter.save(update_fields=["ner_pending"])

    Book.objects.filter(id=chapter.book_id).update(
        ner_completed_count=F("ner_completed_count") + 1
    )

    book = Book.objects.get(id=chapter.book_id)
    if book.ner_completed_count >= book.chapters_count:
        merge_book_ner.delay(book.id)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def merge_book_ner(self, book_id: int):
    from books.models import Book, Chapter
    from .models import BookCharacter, BookPlace, BookOrganization

    book = Book.objects.prefetch_related("chapters").get(id=book_id)
    chapters = list(book.chapters.all())

    char_totals: dict[str, int] = {}
    place_totals: dict[str, int] = {}
    org_totals: dict[str, int] = {}
    full_text_parts: list[str] = []

    for chapter in chapters:
        if chapter.text:
            full_text_parts.append(chapter.text)
        if not chapter.ner_pending:
            continue
        for name, count in chapter.ner_pending.get("characters", {}).items():
            char_totals[name] = char_totals.get(name, 0) + count
        for name, count in chapter.ner_pending.get("locations", {}).items():
            place_totals[name] = place_totals.get(name, 0) + count
        for name, count in chapter.ner_pending.get("organizations", {}).items():
            org_totals[name] = org_totals.get(name, 0) + count

    with transaction.atomic():
        for name, total in char_totals.items():
            char, created = BookCharacter.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                char.mention_count = F("mention_count") + total
                char.save(update_fields=["mention_count"])

        for name, total in place_totals.items():
            place, created = BookPlace.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                place.mention_count = F("mention_count") + total
                place.save(update_fields=["mention_count"])

        for name, total in org_totals.items():
            org, created = BookOrganization.objects.get_or_create(
                name=name, defaults={"mention_count": total}
            )
            if not created:
                org.mention_count = F("mention_count") + total
                org.save(update_fields=["mention_count"])

        chapters_to_update = Chapter.objects.filter(book_id=book_id)
        chapters_to_update.update(text="", ner_pending=None)

    full_text = " ".join(full_text_parts)
    character_names = list(char_totals.keys())

    if full_text and len(character_names) >= 2:
        find_pairs(book_id, full_text, character_names)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def find_pairs(self, book_id: int, full_text: str, character_names: list[str]):
    from .text_parser import find_sentences_with_both_characters

    pairs_data = find_sentences_with_both_characters(full_text, character_names)
    if not pairs_data:
        return

    relations_for_book(book_id, pairs_data)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def relations_for_book(self, book_id: int, pairs_data: list[dict]):
    import json
    from .models import BookCharacter, CharacterRelationship
    from .llm_engine import llm_service

    total_relations = 0
    for item in pairs_data:
        pair = item["pair"]
        sentences = item["sentences"]
        if not sentences:
            continue
        result_json = llm_service.extract_relations_sync(pair, sentences)
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            continue
        for rel in result.get("relations", []):
            try:
                source = BookCharacter.objects.get(name=rel["source"])
                target = BookCharacter.objects.get(name=rel["target"])
                CharacterRelationship.objects.get_or_create(
                    from_character=source,
                    to_character=target,
                    book_id=book_id,
                    defaults={"relation_type": rel["relation"]},
                )
                total_relations += 1
            except BookCharacter.DoesNotExist:
                continue
```

- [ ] **Step 4: Run test — expect PASS**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb uv run python -m pytest analysis/tests/test_tasks.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend-django/analysis/tasks.py backend-django/analysis/tests/test_tasks.py
git commit -m "feat: rewrite Celery tasks to use local engines directly"
```

---

### Task 8: Update views, serializers, and admin

**Files:**
- Modify: `backend-django/books/views.py` — remove auto-trigger, update entity refs
- Modify: `backend-django/books/serializers.py` — update to new entity models
- Modify: `backend-django/books/urls.py` — update character/relation refs if needed
- Create: `backend-django/analysis/admin.py`
- Create: `backend-django/reviews/signals.py`
- Modify: `backend-django/reviews/apps.py`

- [ ] **Step 1: Update books/serializers.py**

Remove old imports and serializers. Add new ones:

```python
# Remove these lines:
from .models import Book, Chapter, BookCharacter, CharacterRelation  # old

# Replace with:
from .models import Book, Chapter
from analysis.models import BookCharacter, CharacterRelationship
```

Replace `BookCharacterSerializer`:
```python
class BookCharacterSerializer(serializers.ModelSerializer):
    mentionCount = serializers.IntegerField(source="mention_count")

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "description", "mentionCount")
```

Replace `CharacterRelationSerializer`:
```python
class CharacterRelationSerializer(serializers.ModelSerializer):
    sourceCharacterName = serializers.CharField(source="from_character.name")
    targetCharacterName = serializers.CharField(source="to_character.name")

    class Meta:
        model = CharacterRelationship
        fields = (
            "id", "sourceCharacterName", "targetCharacterName", "relation_type",
        )
```

In `BookListSerializer`, change `"rating"` → `"avg_rating"`:
```python
fields = (
    ...,
    "avg_rating",   # was "rating"
    "ratings_count",
)
```

In `BookDetailSerializer`, same change:
```python
fields = (
    ...,
    "avg_rating",   # was "rating"
    "ratingsCount",
)
```

In `BookDetailSerializer.to_representation`, update character/relation queries:

```python
# Before (characters from old M2M):
characters = BookCharacterSerializer(
    instance.bookcharacter_set.select_related("character"), many=True
).data

# After (global characters — query all BookCharacter):
characters = BookCharacterSerializer(
    BookCharacter.objects.all(), many=True
).data

# Before (relations from old model):
relations = CharacterRelationSerializer(
    instance.character_relations.select_related("source", "target"), many=True
).data

# After (relations filtered by book):
relations = CharacterRelationSerializer(
    instance.character_relationships.select_related("from_character", "to_character"), many=True
).data
```

- [ ] **Step 2: Update books/views.py**

Remove imports of old models:
```python
# Remove:
from .models import Book, Chapter, BookAuthor, BookCharacter, CharacterRelation
# Replace with:
from .models import Book, Chapter, BookAuthor
from analysis.models import BookCharacter, CharacterRelationship
```

Remove auto-trigger lines from `ChapterView.post`:
```python
# Remove these lines (after chapter creation):
            analyse_chapter.delay(chapter.id, content)
            if chapter_num == 1:
                ner_chapter.delay(chapter.id, content)
```

Replace with no auto-trigger. The admin will trigger via Django Admin action.

Add delete cleanup:
```python
    def delete(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)
        book.chapters.all().delete()
        book.chapters_count = 0
        book.ner_completed_count = 0
        book.save()
        # Clean up relationships for this book
        CharacterRelationship.objects.filter(book_id=book_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

Update `BookDetailView.get_queryset`:
```python
def get_queryset(self):
    return Book.objects.prefetch_related(
        Prefetch("chapters", queryset=Chapter.objects.order_by("chapter_number")),
        Prefetch(
            "character_relationships",
            queryset=CharacterRelationship.objects.select_related(
                "from_character", "to_character"
            ),
        ),
        Prefetch("reviews"),
        "authors",
        "tags",
    )
```

Update `BookCharactersView`:
```python
class BookCharactersView(generics.ListAPIView):
    serializer_class = BookCharacterSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return BookCharacter.objects.all()
```

Update `BookRelationsView`:
```python
class BookRelationsView(generics.ListAPIView):
    serializer_class = CharacterRelationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        return CharacterRelationship.objects.filter(
            book_id=self.kwargs["book_id"]
        ).select_related("from_character", "to_character")
```

- [ ] **Step 3: Create analysis/admin.py**

```python
# backend-django/analysis/admin.py
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404

from analysis.models import BookCharacter, BookPlace, BookOrganization, CharacterRelationship
from analysis.tasks import analyse_chapter, ner_chapter, find_pairs
from analysis.text_parser import split_into_chapters
from books.models import Book, Chapter


@admin.register(BookCharacter)
class BookCharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(BookPlace)
class BookPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(BookOrganization)
class BookOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "mention_count")
    search_fields = ("name",)


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_character", "relation_type", "to_character", "book")
    list_filter = ("relation_type", "book")
    search_fields = ("from_character__name", "to_character__name")


@admin.action(description="Upload book text and split into chapters")
def upload_book_text(modeladmin, request, queryset):
    """This action is meant to be triggered on a single Book.
    The actual file upload form is handled by the Book admin's change form.
    This action triggers analysis on books that already have chapter text."""
    for book in queryset:
        if not book.chapters.exists():
            messages.error(request, f"Book {book.title} has no chapters.")
            continue
        for chapter in book.chapters.all():
            if chapter.text:
                analyse_chapter.delay(chapter.id, chapter.text)
                ner_chapter.delay(chapter.id, chapter.text)
        messages.success(
            request, f"Dispatched analysis for {book.chapters.count()} chapters in '{book.title}'."
        )


@admin.action(description="Analyze selected books (all chapters)")
def analyze_selected_books(modeladmin, request, queryset):
    """Django Admin action — trigger NER+analysis pipeline for selected books."""
    books_triggered = 0
    for book in queryset:
        if not book.chapters.exists():
            continue
        book.ner_completed_count = 0
        book.save()
        for chapter in book.chapters.all():
            if chapter.text:
                analyse_chapter.delay(chapter.id, chapter.text)
                ner_chapter.delay(chapter.id, chapter.text)
        books_triggered += 1
    messages.success(request, f"Analysis dispatched for {books_triggered} books.")
```

Then register the action in the Book admin. Create or modify `backend-django/books/admin.py`:

```python
# backend-django/books/admin.py
from django.contrib import admin
from .models import Book, Chapter
from analysis.admin import upload_book_text, analyze_selected_books


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "chapters_count", "ner_completed_count", "avg_rating")
    actions = [analyze_selected_books]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("chapter_number", "title", "book", "analysis_completed")
```

Make sure `books/admin.py` exists:
```bash
ls backend-django/books/admin.py
```

If not, create it. Check if there's an existing admin registration for Book — if there's already one in `backend-django/books/admin.py`, add the action there.

- [ ] **Step 4: Create reviews/signals.py**

```python
# backend-django/reviews/signals.py
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Review


@receiver(post_save, sender=Review)
@receiver(post_delete, sender=Review)
def update_book_avg_rating(sender, instance, **kwargs):
    from books.models import Book
    result = Review.objects.filter(book=instance.book).aggregate(avg=Avg("rating"))
    avg = result["avg"] or 0.0
    count = Review.objects.filter(book=instance.book).count()
    Book.objects.filter(id=instance.book_id).update(
        avg_rating=round(avg, 2), ratings_count=count
    )
```

- [ ] **Step 5: Update reviews/apps.py**

```python
# backend-django/reviews/apps.py
from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"

    def ready(self):
        import reviews.signals  # noqa
```

- [ ] **Step 6: Run existing tests to verify nothing is broken**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb uv run python manage.py test books -v 2 2>&1 | tail -20
```

Expected: tests may break due to renamed field `rating`→`avg_rating`. Fix any failing tests by updating `rating` references to `avg_rating`.

- [ ] **Step 7: Commit**

```bash
git add backend-django/books/views.py backend-django/books/serializers.py \
        backend-django/books/admin.py backend-django/analysis/admin.py \
        backend-django/reviews/signals.py backend-django/reviews/apps.py
git commit -m "feat: update views, serializers, admin actions, and avg_rating signal"
```

---

### Task 9: Celery queue routing, DLX, Flower

**Files:**
- Modify: `backend-django/config/settings/base.py` — CELERY_TASK_ROUTES
- Create: `infra/rabbitmq/definitions.json`
- Modify: `infra/compose/docker-compose.dev.yml` — split worker, flower, DLX config
- Modify: `infra/compose/docker-compose.prod.yml` — same + fix RabbitMQ v4→v3

- [ ] **Step 1: Add CELERY_TASK_ROUTES to settings**

In `backend-django/config/settings/base.py`, after the existing CELERY config, add:

```python
CELERY_TASK_ROUTES = {
    "analysis.tasks.analyse_chapter": {"queue": "ner"},
    "analysis.tasks.ner_chapter": {"queue": "ner"},
    "analysis.tasks.merge_book_ner": {"queue": "ner"},
    "analysis.tasks.find_pairs": {"queue": "ner"},
    "analysis.tasks.relations_for_book": {"queue": "llm"},
}
```

- [ ] **Step 2: Create RabbitMQ DLX definitions**

```json
{
  "exchanges": [
    {"name": "dlx", "vhost": "/", "type": "direct", "durable": true}
  ],
  "queues": [
    {
      "name": "ner",
      "vhost": "/",
      "durable": true,
      "arguments": {
        "x-dead-letter-exchange": "dlx",
        "x-dead-letter-routing-key": "dead"
      }
    },
    {
      "name": "llm",
      "vhost": "/",
      "durable": true,
      "arguments": {
        "x-dead-letter-exchange": "dlx",
        "x-dead-letter-routing-key": "dead"
      }
    },
    {
      "name": "dead_letter",
      "vhost": "/",
      "durable": true
    }
  ],
  "bindings": [
    {"source": "dlx", "vhost": "/", "destination": "dead_letter", "destination_type": "queue", "routing_key": "dead"}
  ]
}
```

- [ ] **Step 3: Update docker-compose.dev.yml**

Replace `celery-worker` block with two workers:

```yaml
  celery-ner:
    build: ../../backend-django
    container_name: storyshelf-celery-ner
    environment:
      DJANGO_ENV: dev
      DJANGO_SECRET_KEY: dev-secret-key
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-secret-key}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: amqp://rabbitmq:5672//
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - django
      - rabbitmq
    command: celery -A config worker -Q ner -l info -c 2 --pool prefork

  celery-llm:
    build: ../../backend-django
    container_name: storyshelf-celery-llm
    environment:
      DJANGO_ENV: dev
      DJANGO_SECRET_KEY: dev-secret-key
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-secret-key}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: amqp://rabbitmq:5672//
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    depends_on:
      - django
      - rabbitmq
    command: celery -A config worker -Q llm -l info -c 10 --pool gevent

  flower:
    image: mher/flower:2.0
    container_name: storyshelf-flower
    ports:
      - "5555:5555"
    environment:
      CELERY_BROKER_URL: amqp://rabbitmq:5672//
    depends_on:
      - rabbitmq
    command: celery -A config flower --port=5555 --broker=amqp://rabbitmq:5672//
```

Remove the `nlp-service` block entirely.

Add RabbitMQ definitions volume mount to rabbitmq:
```yaml
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: storyshelf-rabbitmq
    ports:
      - "127.0.0.1:15672:15672"
    volumes:
      - ../rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro
    environment:
      RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: -rabbitmq_management load_definitions "/etc/rabbitmq/definitions.json"
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 10s
      timeout: 5s
      retries: 5
```

Remove `hf-cache` volume (was for NLP service).

- [ ] **Step 4: Update docker-compose.prod.yml**

Same split of celery-worker into celery-ner and celery-llm. Add flower. Remove nlp-service. Fix RabbitMQ version to `rabbitmq:3-management-alpine` (was `rabbitmq:4-management-alpine`). Add definitions.json volume mount.

- [ ] **Step 5: Commit**

```bash
git add infra/compose/docker-compose.dev.yml infra/compose/docker-compose.prod.yml \
        infra/rabbitmq/definitions.json backend-django/config/settings/base.py
git commit -m "feat: add queue routing, split workers, DLX, Flower"
```

---

### Task 10: Final cleanup and full test run

- [ ] **Step 1: Remove nlp-service references from .env.example and env files**

Check `.env.example` and `.env` for NLP service related vars. Should already be fine since we removed only the compose service.

- [ ] **Step 2: Run full Django test suite**

```bash
cd backend-django && DJANGO_ENV=dev DATABASE_URL=postgres://postgres:secret-key@localhost:5432/booksdb uv run python manage.py test -v 2
```

Expected: all tests pass. Fix any that reference old models (rating→avg_rating, StoryCharacter→BookCharacter, etc.).

- [ ] **Step 3: Run Django check**

```bash
cd backend-django && DJANGO_ENV=dev uv run python manage.py check
```

- [ ] **Step 4: Update ARCHITECTURE.md to match final state**

Update `ARCHITECTURE.md` with the final entity model, container layout, and data flow as finalized in this plan.

- [ ] **Step 5: Commit**

```bash
git add ARCHITECTURE.md
git commit -m "docs: update ARCHITECTURE.md to match final entity model and flow"
```

---

## Self-Review Checklist

1. **Spec coverage:** All spec requirements covered:
   - [x] NLP service removed (Task 1)
   - [x] NER engine ported (Task 3)
   - [x] LLM engine ported (Task 6)
   - [x] Text stats+parser ported (Task 4)
   - [x] Entity models created (Task 5)
   - [x] Celery tasks rewritten (Task 7)
   - [x] Queue routing + DLX + Flower (Task 9)
   - [x] Admin actions + trigger (Task 8)
   - [x] ShelfEntry fields (Task 5)
   - [x] Review avg_rating signal (Task 8)
   - [x] Compose files updated (Task 9)
   - [x] RabbitMQ v3 fixed (Task 9)
   - [x] Chapter text cleared after merge (Task 7)
   - [x] MISC entities ignored (Task 3 — always returns empty dict)

2. **Placeholder scan:** No TBD, TODO, or placeholder patterns found.

3. **Type consistency:**
   - `ner_pending` JSONField on Chapter in models.py matches tasks.py usage
   - `BookCharacter.name` UNIQUE used consistently in upsert logic
   - `CharacterRelationship.relation_type` (30 chars) matches LLM output schema
   - `find_pairs(full_text, character_names)` signature consistent between `merge_book_ner` call and `find_pairs` definition
   - `Chapter.text` renamed from `Chapter.content` — consistently used in views and tasks
   - `Book.avg_rating` renamed from `Book.rating` — consistently used in serializers

4. **Edge cases covered:**
   - Empty text (split_into_chapters returns [])
   - Single chapter books (no headers → one chapter)
   - Already-processed chapters (skip in tasks)
   - Non-existent BookCharacter in relations (try/except DoesNotExist)
   - LLM returns None content (return empty relations)
   - LLM API errors (return empty relations)
   - No pairs found (find_pairs returns early)
   - merge_book_ner with no F() call for existing entities (increment instead)

---

Plan complete and saved. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
