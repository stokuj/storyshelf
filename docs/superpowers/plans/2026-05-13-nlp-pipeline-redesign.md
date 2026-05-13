# NLP Pipeline Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zastąpić pipeline NER (transformers/BERT) przez spaCy z CPU-only torch, usunąć model `Chapter`, przepisać pipeline Celery na dwa taski per-książka.

**Architecture:** `Book.text` przechowuje tekst do analizy. Jeden task `analyse_book` (kolejka NER) robi spaCy NER na chunkach + find_pairs synchronicznie, po czym woła `relations_for_book.delay()` (kolejka LLM). `BookCharacter`/`BookPlace`/`BookOrganization` zyskują FK do `Book`. Baza resetowana po zmianach schematu.

**Tech Stack:** Django 6, spaCy 3.7 + en_core_web_trf, CPU-only PyTorch, Celery 5.6, DRF 3.17

---

## Pliki do zmiany

| Plik | Zmiana |
|---|---|
| `pyproject.toml` | swap torch→CPU-only, transformers→spacy |
| `analysis/ner_engine.py` | przepisać na spaCy |
| `analysis/models.py` | dodaj `book` FK, usuń global unique na name |
| `books/models.py` | usuń `Chapter`, dodaj `Book.text`, usuń `chapters_count`/`ner_completed_count` |
| `analysis/tasks.py` | usuń stare taski, nowy `analyse_book`, fix `relations_for_book` |
| `books/serializers.py` | usuń `ChapterSerializer`, usuń `chapters` z response, fix `analysisStatus` |
| `books/views.py` | usuń `Chapter` prefetch |
| `books/admin.py` | usuń `ChapterInline`/`ChapterAdmin`, dodaj `text` upload, nowa akcja |
| `analysis/admin.py` | nowa akcja `analyse_book`, dodaj `book` FK do list_display |
| `config/settings/base.py` | zaktualizuj `CELERY_TASK_ROUTES` |
| `analysis/tests/conftest.py` | zaktualizuj fixtures (book FK na character) |
| `analysis/tests/test_tasks.py` | przepisać testy na nowy pipeline |
| `analysis/tests/test_ner_engine.py` | przepisać na spaCy |

---

## Task 1: Swap zależności NLP w pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Krok 1: Zaktualizuj `pyproject.toml`**

Zastąp sekcje `dependencies` i dodaj konfigurację uv sources. Pełna zawartość po zmianie:

```toml
[project]
name = "storyshelf"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "django>=6.0,<6.1",
    "djangorestframework>=3.17",
    "djangorestframework-simplejwt>=5.5",
    "django-cors-headers>=4.9",
    "drf-spectacular>=0.29",
    "celery>=5.6",
    "psycopg2-binary>=2.9",
    "gunicorn>=26.0",
    "dj-database-url>=3.1",
    "redis>=5.2",
    "torch>=2.10",
    "spacy>=3.7",
    "openai>=1.0",
    "tiktoken>=0.7",
    "gevent>=24",
]

[dependency-groups]
dev = [
    "pytest>=9.0.3",
    "pytest-django>=4.12.0",
    "pytest-cov>=6.0",
    "ruff>=0.15.12",
]

[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cpu" }

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N"]

[tool.ruff.lint.per-file-ignores]
"*/migrations/*" = ["E501"]
"*/serializers.py" = ["N815"]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"

[tool.coverage.run]
source = ["."]
omit = ["*/migrations/*", "*/.venv/*", "*/tests/*", "manage.py", "conftest.py"]

[tool.coverage.report]
show_missing = true
skip_covered = false
```

- [ ] **Krok 2: Zainstaluj spaCy i model**

```bash
cd backend-django
uv sync
uv run python -m spacy download en_core_web_trf
```

Oczekiwane: brak błędów, `en_core_web_trf` zainstalowany.

- [ ] **Krok 3: Verify**

```bash
uv run python -c "import spacy; nlp = spacy.load('en_core_web_trf'); print('spaCy OK')"
uv run python -c "import torch; print('torch:', torch.__version__)"
```

Oczekiwane: `spaCy OK`, `torch: 2.x.x+cpu`

- [ ] **Krok 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: swap transformers/BERT for spaCy en_core_web_trf with CPU-only torch"
```

---

## Task 2: Przepisz NER engine na spaCy

**Files:**
- Modify: `analysis/ner_engine.py`
- Modify: `analysis/tests/test_ner_engine.py`

- [ ] **Krok 1: Napisz testy (TDD)**

Zastąp całą zawartość `analysis/tests/test_ner_engine.py`:

```python
from unittest.mock import MagicMock, patch


def make_ent(text, label):
    ent = MagicMock()
    ent.text = text
    ent.label_ = label
    return ent


def make_doc(ents):
    doc = MagicMock()
    doc.ents = ents
    return doc


class TestChunkText:
    def test_single_chunk_for_short_text(self):
        from analysis.ner_engine import chunk_text

        chunks = chunk_text("word " * 100, chunk_size=400, overlap=50)
        assert len(chunks) == 1

    def test_multiple_chunks_for_long_text(self):
        from analysis.ner_engine import chunk_text

        chunks = chunk_text("word " * 1000, chunk_size=400, overlap=50)
        assert len(chunks) > 1

    def test_overlap_means_chunks_share_words(self):
        from analysis.ner_engine import chunk_text

        text = " ".join(str(i) for i in range(500))
        chunks = chunk_text(text, chunk_size=400, overlap=50)
        last_words_of_first = set(chunks[0].split()[-50:])
        first_words_of_second = set(chunks[1].split()[:50])
        assert last_words_of_first & first_words_of_second


class TestExtractEntitiesFromChunks:
    def test_aggregates_characters_across_chunks(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Frodo", "PERSON")]),
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Gandalf", "PERSON")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["characters"]["Frodo"] == 3
        assert result["characters"]["Gandalf"] == 1

    def test_filters_by_min_occurrences(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Frodo", "PERSON"), make_ent("Rare", "PERSON")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 2):
                result = extract_entities_from_chunks("some text")

        assert "Frodo" not in result["characters"]
        assert "Rare" not in result["characters"]

    def test_returns_empty_when_nlp_fails(self):
        from analysis.ner_engine import extract_entities_from_chunks

        with patch("analysis.ner_engine._get_nlp", return_value=None):
            result = extract_entities_from_chunks("some text")

        assert result == {}

    def test_loc_goes_to_locations(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Shire", "LOC")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["locations"]["Shire"] == 1

    def test_org_goes_to_organizations(self):
        from analysis.ner_engine import extract_entities_from_chunks

        mock_nlp = MagicMock()
        mock_nlp.pipe.return_value = iter([
            make_doc([make_ent("Fellowship", "ORG")]),
        ])
        with patch("analysis.ner_engine._get_nlp", return_value=mock_nlp):
            with patch("analysis.ner_engine.NER_MIN_OCCURRENCES", 1):
                result = extract_entities_from_chunks("some text")

        assert result["organizations"]["Fellowship"] == 1
```

- [ ] **Krok 2: Uruchom testy — powinny failować**

```bash
DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_ner_engine.py -v
```

Oczekiwane: ImportError lub AttributeError — `chunk_text`/`extract_entities_from_chunks` nie istnieją.

- [ ] **Krok 3: Przepisz `analysis/ner_engine.py`**

```python
from __future__ import annotations

import logging
import os
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_NER_MODEL = os.getenv("NER_MODEL", "en_core_web_trf")
NER_MIN_OCCURRENCES = int(os.getenv("NER_MIN_OCCURRENCES", "5"))

_NLP: dict[str, Any] = {}

LABEL_MAP = {
    "PERSON": "characters",
    "PER": "characters",
    "ORG": "organizations",
    "LOC": "locations",
    "GPE": "locations",
}


def _get_nlp(model: str = DEFAULT_NER_MODEL) -> Any | None:
    if model in _NLP:
        return _NLP[model]
    try:
        import spacy

        logger.info("Loading spaCy model: %s", model)
        _NLP[model] = spacy.load(model)
        logger.info("spaCy model loaded: %s", model)
        return _NLP[model]
    except (OSError, ImportError) as exc:
        logger.warning("spaCy model '%s' unavailable: %s", model, exc)
        return None


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = chunk_size - overlap
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_entities_from_chunks(
    text: str,
    model: str = DEFAULT_NER_MODEL,
    chunk_size: int = 400,
    overlap: int = 50,
) -> dict:
    nlp = _get_nlp(model)
    if nlp is None:
        return {}

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        return {}

    raw: dict[str, list[str]] = {
        "characters": [],
        "organizations": [],
        "locations": [],
    }

    for doc in nlp.pipe(chunks, batch_size=8):
        for ent in doc.ents:
            key = LABEL_MAP.get(ent.label_)
            if key:
                raw[key].append(ent.text.strip())

    def filtered_counts(names: list[str]) -> dict[str, int]:
        counts = Counter(names)
        return {
            n: c
            for n, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)
            if c >= NER_MIN_OCCURRENCES
        }

    return {
        "characters": filtered_counts(raw["characters"]),
        "organizations": filtered_counts(raw["organizations"]),
        "locations": filtered_counts(raw["locations"]),
    }
```

- [ ] **Krok 4: Uruchom testy — powinny przejść**

```bash
DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_ner_engine.py -v
```

Oczekiwane: wszystkie PASS.

- [ ] **Krok 5: Commit**

```bash
git add analysis/ner_engine.py analysis/tests/test_ner_engine.py
git commit -m "feat: replace transformers/BERT NER engine with spaCy en_core_web_trf"
```

---

## Task 3: Zaktualizuj modele — book FK na encje, usuń Chapter

**Files:**
- Modify: `analysis/models.py`
- Modify: `books/models.py`
- Modify: `analysis/tests/conftest.py`

- [ ] **Krok 1: Zaktualizuj `analysis/models.py`**

Dodaj `book` FK do `BookCharacter`, `BookPlace`, `BookOrganization`. Usuń `unique=True` z `name`, dodaj `unique_together`:

```python
from django.db import models


class BookCharacter(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="characters"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("name", "book")

    def __str__(self):
        return self.name


class BookPlace(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="places"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("name", "book")

    def __str__(self):
        return self.name


class BookOrganization(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="organizations"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    mention_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("name", "book")

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

- [ ] **Krok 2: Zaktualizuj `books/models.py`**

Usuń `Chapter`, dodaj `Book.text`, usuń `chapters_count` i `ner_completed_count`:

```python
from django.core.validators import MinValueValidator
from django.db import models


class Book(models.Model):
    serie = models.ForeignKey(
        "library.Serie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books",
    )
    title = models.CharField(max_length=500)
    year = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    isbn = models.CharField(max_length=20, unique=True, null=True, blank=True, default=None)
    description = models.TextField(blank=True, default="")
    page_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    position_in_series = models.IntegerField(null=True, blank=True)
    text = models.TextField(blank=True, default="")
    avg_rating = models.FloatField(default=0.0)
    ratings_count = models.IntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)
    authors = models.ManyToManyField("library.Author", through="BookAuthor")
    tags = models.ManyToManyField("library.Tag", through="BookTag")
    genres = models.ManyToManyField("library.Genre", through="BookGenre", related_name="books")


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


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="book_genres")
    genre = models.ForeignKey(
        "library.Genre", on_delete=models.CASCADE, related_name="book_genres"
    )

    class Meta:
        unique_together = ["book", "genre"]
```

- [ ] **Krok 3: Zaktualizuj `analysis/tests/conftest.py`**

Fixtures `character_a` i `character_b` muszą mieć `book` FK:

```python
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def django_db_setup():
    pass


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def book(db):
    from books.models import Book

    return Book.objects.create(title="Test Book", year=2020, page_count=100)


@pytest.fixture
def character_a(db, book):
    from analysis.models import BookCharacter

    return BookCharacter.objects.create(name="Frodo", book=book)


@pytest.fixture
def character_b(db, book):
    from analysis.models import BookCharacter

    return BookCharacter.objects.create(name="Sam", book=book)
```

- [ ] **Krok 4: Utwórz migracje**

```bash
cd backend-django
uv run python manage.py makemigrations analysis books
```

Oczekiwane: nowe pliki migracji w `analysis/migrations/` i `books/migrations/`.

- [ ] **Krok 5: Reset DB i migruj**

```bash
DJANGO_ENV=dev uv run python manage.py flush --no-input
DJANGO_ENV=dev uv run python manage.py migrate
```

Oczekiwane: `OK` bez błędów.

- [ ] **Krok 6: System check**

```bash
uv run python manage.py check
```

Oczekiwane: `System check identified no issues (0 silenced).`

- [ ] **Krok 7: Commit**

```bash
git add analysis/models.py books/models.py analysis/tests/conftest.py analysis/migrations/ books/migrations/
git commit -m "feat: add book FK to entity models, remove Chapter model, add Book.text"
```

---

## Task 4: Przepisz analysis/tasks.py

**Files:**
- Modify: `analysis/tasks.py`
- Modify: `analysis/tests/test_tasks.py`

- [ ] **Krok 1: Napisz testy (TDD)**

Zastąp całą zawartość `analysis/tests/test_tasks.py`:

```python
from unittest.mock import patch


class TestAnalyseBook:
    def test_skips_if_no_text(self, db, book):
        from analysis.tasks import analyse_book

        analyse_book(book.id)

        from analysis.models import BookCharacter
        assert not BookCharacter.objects.filter(book=book).exists()

    def test_creates_characters_from_ner(self, db, book):
        book.text = "Frodo walked in the Shire with Gandalf."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 3, "Gandalf": 2},
                "locations": {"Shire": 1},
                "organizations": {},
            }
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                mock_llm.delay = lambda *a, **kw: None
                from analysis.tasks import analyse_book
                analyse_book(book.id)

        from analysis.models import BookCharacter, BookPlace
        assert BookCharacter.objects.filter(book=book, name="Frodo").exists()
        assert BookCharacter.objects.filter(book=book, name="Gandalf").exists()
        assert BookPlace.objects.filter(book=book, name="Shire").exists()

    def test_clears_text_after_analysis(self, db, book):
        book.text = "Frodo and Gandalf went to the Shire."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {"characters": {}, "locations": {}, "organizations": {}}
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                mock_llm.delay = lambda *a, **kw: None
                from analysis.tasks import analyse_book
                analyse_book(book.id)

        book.refresh_from_db()
        assert book.text == ""

    def test_dispatches_relations_task_when_pairs_found(self, db, book):
        book.text = "Frodo and Sam walked together."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 2, "Sam": 2},
                "locations": {},
                "organizations": {},
            }
            with patch("analysis.tasks.find_sentences_with_both_characters") as mock_fp:
                mock_fp.return_value = [{"pair": ["Frodo", "Sam"], "sentences": ["Frodo and Sam walked."]}]
                with patch("analysis.tasks.relations_for_book") as mock_llm:
                    from analysis.tasks import analyse_book
                    analyse_book(book.id)
                    mock_llm.delay.assert_called_once()

    def test_no_llm_dispatch_when_fewer_than_two_characters(self, db, book):
        book.text = "Frodo walked alone."
        book.save()

        with patch("analysis.tasks.extract_entities_from_chunks") as mock_ner:
            mock_ner.return_value = {
                "characters": {"Frodo": 1},
                "locations": {},
                "organizations": {},
            }
            with patch("analysis.tasks.relations_for_book") as mock_llm:
                from analysis.tasks import analyse_book
                analyse_book(book.id)
                mock_llm.delay.assert_not_called()


class TestRelationsForBook:
    def test_skips_pair_on_api_error(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        char_a = BookCharacter.objects.create(name="Frodo", book=book)
        char_b = BookCharacter.objects.create(name="Sam", book=book)

        pairs_data = [{"pair": ["Frodo", "Sam"], "sentences": ["Frodo and Sam walked."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = '{"relations": []}'
            from analysis.tasks import relations_for_book
            relations_for_book(book.id, pairs_data)

        assert not CharacterRelationship.objects.filter(book=book).exists()

    def test_saves_valid_relation(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        BookCharacter.objects.create(name="Frodo", book=book)
        BookCharacter.objects.create(name="Gandalf", book=book)

        pairs_data = [{"pair": ["Frodo", "Gandalf"], "sentences": ["Gandalf mentored Frodo."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = (
                '{"relations": [{"source": "Frodo", "relation": "mentor_of",'
                ' "target": "Gandalf", "evidence": "..."}]}'
            )
            from analysis.tasks import relations_for_book
            relations_for_book(book.id, pairs_data)

        assert CharacterRelationship.objects.filter(book=book).count() == 1

    def test_skips_unknown_character(self, db, book):
        from analysis.models import BookCharacter, CharacterRelationship

        BookCharacter.objects.create(name="Frodo", book=book)

        pairs_data = [{"pair": ["Frodo", "Ghost"], "sentences": ["Frodo met Ghost."]}]

        with patch("analysis.tasks.llm_service") as mock_llm:
            mock_llm.extract_relations.return_value = (
                '{"relations": [{"source": "Frodo", "relation": "friend_of",'
                ' "target": "Ghost", "evidence": "..."}]}'
            )
            from analysis.tasks import relations_for_book
            relations_for_book(book.id, pairs_data)

        assert not CharacterRelationship.objects.filter(book=book).exists()
```

- [ ] **Krok 2: Uruchom testy — powinny failować**

```bash
DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_tasks.py -v
```

Oczekiwane: ImportError lub AttributeError.

- [ ] **Krok 3: Przepisz `analysis/tasks.py`**

```python
import json
import logging

from celery import shared_task
from django.db import transaction

from .ner_engine import extract_entities_from_chunks
from .text_parser import find_sentences_with_both_characters

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def analyse_book(self, book_id: int):
    from books.models import Book

    from .llm_engine import llm_service
    from .models import BookCharacter, BookOrganization, BookPlace

    book = Book.objects.get(id=book_id)
    if not book.text:
        return

    full_text = book.text

    result = extract_entities_from_chunks(full_text)

    char_names: list[str] = []
    with transaction.atomic():
        for name, count in result.get("characters", {}).items():
            BookCharacter.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )
            char_names.append(name)

        for name, count in result.get("locations", {}).items():
            BookPlace.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )

        for name, count in result.get("organizations", {}).items():
            BookOrganization.objects.update_or_create(
                name=name, book=book, defaults={"mention_count": count}
            )

    pairs_data = find_sentences_with_both_characters(full_text, char_names)

    Book.objects.filter(id=book_id).update(text="")

    if pairs_data and len(char_names) >= 2:
        relations_for_book.delay(book_id, pairs_data)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def relations_for_book(self, book_id: int, pairs_data: list[dict]):
    from .llm_engine import llm_service
    from .models import BookCharacter, CharacterRelationship

    for item in pairs_data:
        pair = item["pair"]
        sentences = item["sentences"]
        if not sentences:
            continue
        try:
            result_json = llm_service.extract_relations(pair, sentences)
            result = json.loads(result_json)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("LLM error for pair %s: %s", pair, e)
            continue

        for rel in result.get("relations", []):
            try:
                source = BookCharacter.objects.get(name=rel["source"], book_id=book_id)
                target = BookCharacter.objects.get(name=rel["target"], book_id=book_id)
                CharacterRelationship.objects.get_or_create(
                    from_character=source,
                    to_character=target,
                    book_id=book_id,
                    defaults={"relation_type": rel["relation"]},
                )
            except BookCharacter.DoesNotExist:
                logger.warning("Character not found for relation: %s", rel)
                continue
```

- [ ] **Krok 4: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python -m pytest analysis/tests/test_tasks.py -v
```

Oczekiwane: wszystkie PASS.

- [ ] **Krok 5: Commit**

```bash
git add analysis/tasks.py analysis/tests/test_tasks.py
git commit -m "feat: rewrite Celery pipeline — analyse_book + fix relations_for_book"
```

---

## Task 5: Zaktualizuj serializers, views, admin, config

**Files:**
- Modify: `books/serializers.py`
- Modify: `books/views.py`
- Modify: `books/admin.py`
- Modify: `analysis/admin.py`
- Modify: `config/settings/base.py`

- [ ] **Krok 1: Zaktualizuj `books/serializers.py`**

Usuń `ChapterSerializer` i `chapters` z response. Zaktualizuj `analysisStatus` i query dla characters:

```python
from django.db.models import Q
from rest_framework import serializers

from analysis.models import BookCharacter, CharacterRelationship

from .models import Book


class BookCharacterSerializer(serializers.ModelSerializer):
    mentionCount = serializers.IntegerField(source="mention_count")  # noqa: N815

    class Meta:
        model = BookCharacter
        fields = ("id", "name", "description", "mentionCount")


class CharacterRelationSerializer(serializers.ModelSerializer):
    sourceCharacterName = serializers.CharField(source="from_character.name")  # noqa: N815
    targetCharacterName = serializers.CharField(source="to_character.name")  # noqa: N815

    class Meta:
        model = CharacterRelationship
        fields = (
            "id",
            "sourceCharacterName",
            "targetCharacterName",
            "relation_type",
        )


class BookSerializerMixin:
    def get_author(self, obj):
        return obj.authors.first().name if obj.authors.exists() else None

    def get_genres(self, obj):
        return [g.name for g in obj.genres.all()]

    def get_tags(self, obj):
        return [t.name for t in obj.tags.all()]


class BookListSerializer(BookSerializerMixin, serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "year",
            "isbn",
            "description",
            "page_count",
            "genres",
            "tags",
            "avg_rating",
            "ratings_count",
        )


class BookDetailSerializer(BookSerializerMixin, serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    ratingsCount = serializers.IntegerField(source="ratings_count")  # noqa: N815

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "year",
            "isbn",
            "description",
            "page_count",
            "genres",
            "tags",
            "avg_rating",
            "ratingsCount",
        )

    def to_representation(self, instance):
        request = self.context.get("request")
        book_data = super().to_representation(instance)

        book_data["analysisStatus"] = {
            "analysisFinished": BookCharacter.objects.filter(book=instance).exists(),
        }

        if instance.serie:
            book_data["series"] = {"name": instance.serie.name}
        book_data["seriesName"] = instance.serie.name if instance.serie else None
        book_data["seriesTitle"] = None

        shelf_entry = None
        if request and request.user.is_authenticated:
            try:
                entry = instance.shelf_entries.get(user=request.user)
                shelf_entry = {
                    "status": entry.status,
                    "createdAt": entry.created_at.isoformat(),
                }
            except Exception:
                pass

        characters = BookCharacterSerializer(
            BookCharacter.objects.filter(book=instance),
            many=True,
        ).data

        relations = CharacterRelationSerializer(
            instance.character_relationships.select_related("from_character", "to_character"),
            many=True,
        ).data

        return {
            "book": book_data,
            "shelfEntry": shelf_entry,
            "characters": characters,
            "relations": relations,
        }
```

- [ ] **Krok 2: Zaktualizuj `books/views.py`**

Usuń `Chapter` i `CharacterRelationship` z prefetch w `BookRetrieveView`:

```python
from django.db.models import Prefetch, Q
from rest_framework import generics, permissions

from .models import Book
from .serializers import BookDetailSerializer, BookListSerializer


class BookListView(generics.ListAPIView):
    """
    Zwraca płaską listę wszystkich książek.
    Filtrowanie pełnotekstowe: ?q=<fraza> — przeszukuje tytuł, nazwisko autora i gatunek.
    """

    serializer_class = BookListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        qs = Book.objects.select_related("serie").prefetch_related("authors", "tags", "genres")
        q = self.request.query_params.get("q", "")
        if q:
            q_lower = q.lower()
            qs = qs.filter(
                Q(title__icontains=q_lower)
                | Q(bookauthor__author__name__icontains=q_lower)
                | Q(genres__name__icontains=q_lower)
            ).distinct()
        return qs


class BookRetrieveView(generics.RetrieveAPIView):
    """
    Szczegóły książki wraz z relacjami między postaciami, autorami, tagami i gatunkami.
    """

    serializer_class = BookDetailSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Book.objects.prefetch_related(
            "authors",
            "tags",
            "genres",
            "characters",
            "character_relationships__from_character",
            "character_relationships__to_character",
        )
```

- [ ] **Krok 3: Zaktualizuj `books/admin.py`**

Usuń `ChapterInline`, `ChapterAdmin`, dodaj pole `text`:

```python
from django.contrib import admin

from analysis.admin import analyze_selected_books

from .models import Book, BookAuthor


class BookAuthorInline(admin.TabularInline):
    model = BookAuthor
    extra = 1


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "avg_rating", "ratings_count")
    search_fields = ("title", "bookauthor__author__name")
    inlines = [BookAuthorInline]
    actions = [analyze_selected_books]
    fields = (
        "title", "year", "isbn", "description", "page_count",
        "serie", "position_in_series", "text",
        "avg_rating", "ratings_count",
    )
```

- [ ] **Krok 4: Zaktualizuj `analysis/admin.py`**

Nowa akcja używa `analyse_book`, zaktualizuj `list_display` o `book`:

```python
from django.contrib import admin, messages

from analysis.models import (
    BookCharacter,
    BookOrganization,
    BookPlace,
    CharacterRelationship,
)
from analysis.tasks import analyse_book


@admin.register(BookCharacter)
class BookCharacterAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(BookPlace)
class BookPlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(BookOrganization)
class BookOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "book", "mention_count")
    search_fields = ("name",)
    list_filter = ("book",)


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_character", "relation_type", "to_character", "book")
    list_filter = ("relation_type", "book")
    search_fields = ("from_character__name", "to_character__name")


@admin.action(description="Analyse selected books (NER + LLM)")
def analyze_selected_books(modeladmin, request, queryset):
    triggered = 0
    for book in queryset:
        if not book.text:
            continue
        analyse_book.delay(book.id)
        triggered += 1
    messages.success(request, f"Analysis dispatched for {triggered} books.")
```

- [ ] **Krok 5: Zaktualizuj `CELERY_TASK_ROUTES` w `config/settings/base.py`**

Zastąp stare wpisy:

```python
CELERY_TASK_ROUTES = {
    "analysis.tasks.analyse_book": {"queue": "ner"},
    "analysis.tasks.relations_for_book": {"queue": "llm"},
}
```

- [ ] **Krok 6: Uruchom testy**

```bash
DJANGO_ENV=dev uv run python manage.py test books -v 2
```

Oczekiwane: wszystkie PASS (brak testów dla Chapter — usunięte).

- [ ] **Krok 7: Lint**

```bash
uv run ruff check .
```

Oczekiwane: brak błędów.

- [ ] **Krok 8: Commit**

```bash
git add books/serializers.py books/views.py books/admin.py analysis/admin.py config/settings/base.py
git commit -m "feat: remove Chapter from API response, update admin and celery routes"
```

---

## Task 6: Pełna weryfikacja

- [ ] **Krok 1: Uruchom wszystkie testy**

```bash
DJANGO_ENV=dev uv run python manage.py test -v 2 2>&1 | tail -10
DJANGO_ENV=dev uv run python -m pytest analysis/tests/ -v
```

Oczekiwane: wszystkie zielone.

- [ ] **Krok 2: Lint**

```bash
uv run ruff check .
```

Oczekiwane: exit 0.

- [ ] **Krok 3: System check + migracje aktualne**

```bash
uv run python manage.py check
DJANGO_ENV=dev uv run python manage.py migrate --check
```

- [ ] **Krok 4: Seed data**

```bash
DJANGO_ENV=dev uv run python ../infra/scripts/seed.py
```

- [ ] **Krok 5: Ręczny test pipeline (Django shell)**

```bash
DJANGO_ENV=dev uv run python manage.py shell
```

```python
from books.models import Book
from analysis.tasks import analyse_book

b = Book.objects.first()
b.text = """
Frodo Baggins lived in the Shire. Gandalf visited Frodo often.
Gandalf gave Frodo the One Ring. Frodo trusted Gandalf completely.
Sam Gamgee was Frodo's gardener. Sam accompanied Frodo on his journey.
Frodo and Sam left the Shire together. Gandalf warned Frodo about Sauron.
"""
b.save()
analyse_book(b.id)  # synchronous in DJANGO_ENV=dev (CELERY_TASK_ALWAYS_EAGER=True)

from analysis.models import BookCharacter, CharacterRelationship
print(list(BookCharacter.objects.filter(book=b).values('name', 'mention_count')))
print(CharacterRelationship.objects.filter(book=b).count())
```

Oczekiwane: lista postaci z mention_count, relacje w DB.

- [ ] **Krok 6: Final commit**

```bash
git add -A
git commit -m "chore: NLP pipeline redesign complete — spaCy, per-book entities, simplified tasks"
```
