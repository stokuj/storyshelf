# M13 AI Character Analysis Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-book character section (monogram cards) with per-character subpages and an ego relation graph, generated on demand by an LLM via OpenRouter, processed asynchronously with Celery + Redis.

**Architecture:** New Django app `characters/` holds three models (`CharacterAnalysis` lifecycle, `Character`, `CharacterRelation`). A `POST .../generate/` endpoint enqueues a Celery task (idempotent per book); the worker calls OpenRouter (one structured-JSON HTTP call via stdlib `urllib`), validates, and stores up to 12 characters + relations in one transaction. Frontend renders the section on `/books/[slug]`, polls until done, and a subpage `/books/[slug]/characters/[charSlug]/` shows a hand-rolled SVG ego-graph with clickable nodes.

**Tech Stack:** Django 6 + DRF, Celery 5 + Redis 7, OpenRouter (stdlib `urllib`), SvelteKit 2 / Svelte 5, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-06-05-m13-ai-characters-design.md`

---

## File Structure

**Backend (new app `backend-django/characters/`):**
- `apps.py` — `CharactersConfig`
- `models.py` — `CharacterAnalysis`, `Character`, `CharacterRelation`
- `ai.py` — `generate_characters(book)` OpenRouter client + `CharacterGenerationError`
- `services.py` — `store_characters(book, data)` (delete-and-replace in a transaction)
- `tasks.py` — `generate_characters_task(book_id)` Celery task
- `serializers.py` — `CharacterListSerializer`, `CharacterDetailSerializer`, `CharacterListResponseSerializer`
- `views.py` — `GenerateCharactersView`, `CharacterListView`, `CharacterDetailView`
- `urls.py` — three routes
- `tests/test_ai.py`, `tests/test_services.py`, `tests/test_tasks.py`, `tests/test_api.py`

**Backend (modified):**
- `config/celery.py` (new), `config/__init__.py`, `config/settings/base.py`, `config/settings/dev.py`, `config/urls.py`
- `pyproject.toml`

**Infra (modified):**
- `infra/compose/docker-compose.dev.yml`, `Makefile`, `infra/.env.example`

**Frontend (new):**
- `svelte-frontend/src/lib/types/character.ts`
- `svelte-frontend/src/lib/api/characters.ts`
- `svelte-frontend/src/lib/utils/monogram.ts`
- `svelte-frontend/src/lib/components/character/CharacterCard.svelte`
- `svelte-frontend/src/lib/components/character/CharacterSection.svelte`
- `svelte-frontend/src/lib/components/character/RelationGraph.svelte`
- `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.server.ts`
- `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.svelte`

**Frontend (modified):**
- `svelte-frontend/src/routes/books/[slug]/+page.server.ts`, `+page.svelte`

**Docs (modified/new):**
- `docs/decisions/ADR-003-celery-redis-llm.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/api/openapi.yml`

---

## Task 1: Add Celery + Redis dependencies and Celery app

**Files:**
- Modify: `backend-django/pyproject.toml`
- Create: `backend-django/config/celery.py`
- Modify: `backend-django/config/__init__.py`
- Modify: `backend-django/config/settings/base.py`
- Modify: `backend-django/config/settings/dev.py`

- [ ] **Step 1: Add deps to pyproject.toml**

In `backend-django/pyproject.toml`, add to the `dependencies` list (after `"Pillow>=11.0",`):

```toml
    "celery>=5.4",
    "redis>=5.2",
```

- [ ] **Step 2: Sync the environment**

Run: `cd backend-django && uv sync`
Expected: resolves and installs `celery` and `redis`.

- [ ] **Step 3: Create the Celery app**

Create `backend-django/config/celery.py`:

```python
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("storyshelf")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- [ ] **Step 4: Load the Celery app on Django startup**

Replace the contents of `backend-django/config/__init__.py` (currently empty) with:

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

- [ ] **Step 5: Add Celery + OpenRouter settings**

In `backend-django/config/settings/base.py`, append at the end of the file:

```python
# --- Celery (background tasks) ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))

# --- OpenRouter (characters/ai.py) ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-haiku")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
```

- [ ] **Step 6: Run Celery tasks eagerly under tests**

In `backend-django/config/settings/dev.py`, inside the existing `if _IS_TEST_RUN:` block, add after the `REST_FRAMEWORK = {...}` line:

```python
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
```

- [ ] **Step 7: Verify Django still boots**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 8: Commit**

```bash
git add backend-django/pyproject.toml backend-django/uv.lock backend-django/config/
git commit -m "chore: wire Celery + Redis and OpenRouter settings"
```

---

## Task 2: Add Redis + Celery worker to the dev stack

**Files:**
- Modify: `infra/compose/docker-compose.dev.yml`
- Modify: `Makefile`
- Modify: `infra/.env.example`

- [ ] **Step 1: Add redis + celery services**

In `infra/compose/docker-compose.dev.yml`, add a `redis` service and a `celery` service. Insert the `celery` service right after the `django` service block, and `redis` before `db`. Add `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` / `OPENROUTER_*` to the `django` service `environment` too (the API process imports the task).

`celery` service (same image as django, different command):

```yaml
  celery:
    build: ../../backend-django
    container_name: storyshelf-celery
    volumes:
      - ../../backend-django:/app
      - /app/.venv
      - media:/app/media
    environment:
      DJANGO_ENV: dev
      DJANGO_SECRET_KEY: dev-secret-key
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-secret-key}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}
      OPENROUTER_MODEL: ${OPENROUTER_MODEL:-anthropic/claude-3.5-haiku}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    command: celery -A config worker --loglevel=info --concurrency=4
```

`redis` service:

```yaml
  redis:
    image: redis:7
    container_name: storyshelf-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
```

In the existing `django` service `environment:` block, add these three lines:

```yaml
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-}
      OPENROUTER_MODEL: ${OPENROUTER_MODEL:-anthropic/claude-3.5-haiku}
```

And add `redis` to the `django` service `depends_on:`:

```yaml
      redis:
        condition: service_started
```

- [ ] **Step 2: Document env vars**

In `infra/.env.example`, add:

```bash
# OpenRouter (AI character generation — M13)
OPENROUTER_API_KEY=
OPENROUTER_MODEL=anthropic/claude-3.5-haiku
```

- [ ] **Step 3: Update dev-up output**

In `Makefile`, in the `dev-up` target, add one printf line after the admin panel line:

```makefile
	@printf '%s\n' '  redis: localhost:6379 · celery worker: storyshelf-celery'
```

- [ ] **Step 4: Validate compose file**

Run: `docker compose -f infra/compose/docker-compose.dev.yml --env-file infra/.env config -q`
Expected: no output (valid). If `infra/.env` is missing, use `infra/.env.example` instead.

- [ ] **Step 5: Commit**

```bash
git add infra/compose/docker-compose.dev.yml infra/.env.example Makefile
git commit -m "chore: add redis + celery worker to dev stack"
```

---

## Task 3: Create the `characters` app, models, and migration

**Files:**
- Create: `backend-django/characters/__init__.py`, `apps.py`, `models.py`
- Create: `backend-django/characters/tests/__init__.py`
- Modify: `backend-django/config/settings/base.py`

- [ ] **Step 1: Scaffold the app package**

Create `backend-django/characters/__init__.py` (empty file) and `backend-django/characters/tests/__init__.py` (empty file).

Create `backend-django/characters/apps.py`:

```python
from django.apps import AppConfig


class CharactersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "characters"
```

- [ ] **Step 2: Register the app**

In `backend-django/config/settings/base.py`, add to `INSTALLED_APPS` after `"feed.apps.FeedConfig",`:

```python
    "characters.apps.CharactersConfig",
```

- [ ] **Step 3: Write the models**

Create `backend-django/characters/models.py`:

```python
from django.db import models
from django.utils.text import slugify


def unique_character_slug(book, name: str) -> str:
    """Slug unique within one book. Dedups with a numeric suffix."""
    base = slugify(name)[:200] or "character"
    slug = base
    counter = 1
    while Character.objects.filter(book=book, slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class CharacterAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    book = models.OneToOneField(
        "books.Book", on_delete=models.CASCADE, related_name="character_analysis"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default="")
    model = models.CharField(max_length=200, blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.book.title} [{self.status}]"


class Character(models.Model):
    book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name="characters")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    role = models.CharField(max_length=120, blank=True, default="")
    description = models.TextField(blank=True, default="")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        constraints = [
            models.UniqueConstraint(fields=["book", "slug"], name="unique_book_character_slug"),
        ]

    def __str__(self):
        return f"{self.name} ({self.book.title})"


class CharacterRelation(models.Model):
    book = models.ForeignKey(
        "books.Book", on_delete=models.CASCADE, related_name="character_relations"
    )
    from_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="relations_from"
    )
    to_character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="relations_to"
    )
    label = models.CharField(max_length=120)

    def __str__(self):
        return f"{self.from_character.name} → {self.to_character.name} ({self.label})"
```

- [ ] **Step 4: Make the migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations characters`
Expected: `Migrations for 'characters': characters/migrations/0001_initial.py` with three models.

- [ ] **Step 5: Apply the migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py migrate characters`
Expected: `Applying characters.0001_initial... OK`.

- [ ] **Step 6: Commit**

```bash
git add backend-django/characters/ backend-django/config/settings/base.py
git commit -m "feat: add characters app models and migration"
```

---

## Task 4: OpenRouter client (`characters/ai.py`)

**Files:**
- Create: `backend-django/characters/ai.py`
- Create: `backend-django/characters/tests/test_ai.py`

- [ ] **Step 1: Write the failing test**

Create `backend-django/characters/tests/test_ai.py`:

```python
import json
from unittest.mock import patch

from django.test import TestCase, override_settings

from characters.ai import CharacterGenerationError, generate_characters


class FakeBook:
    title = "Dune"

    class _Authors:
        def values_list(self, *a, **k):
            return ["Frank Herbert"]

    authors = _Authors()


def _openrouter_response(payload: dict) -> bytes:
    content = json.dumps(payload)
    return json.dumps({"choices": [{"message": {"content": content}}]}).encode("utf-8")


@override_settings(OPENROUTER_API_KEY="test-key", OPENROUTER_MODEL="test/model")
class GenerateCharactersTests(TestCase):
    def test_parses_characters_and_relations(self):
        body = _openrouter_response(
            {
                "characters": [
                    {"name": "Paul Atreides", "role": "Protagonist", "description": "Heir."},
                ],
                "relations": [
                    {"from": "Paul Atreides", "to": "Lady Jessica", "label": "son"},
                ],
            }
        )

        class _Resp:
            def __enter__(self_):
                return self_

            def __exit__(self_, *a):
                return False

            def read(self_):
                return body

        with patch("characters.ai.urllib.request.urlopen", return_value=_Resp()):
            data = generate_characters(FakeBook())

        self.assertEqual(data["characters"][0]["name"], "Paul Atreides")
        self.assertEqual(data["relations"][0]["label"], "son")

    def test_invalid_json_raises(self):
        body = json.dumps({"choices": [{"message": {"content": "not json"}}]}).encode("utf-8")

        class _Resp:
            def __enter__(self_):
                return self_

            def __exit__(self_, *a):
                return False

            def read(self_):
                return body

        with patch("characters.ai.urllib.request.urlopen", return_value=_Resp()):
            with self.assertRaises(CharacterGenerationError):
                generate_characters(FakeBook())

    @override_settings(OPENROUTER_API_KEY="")
    def test_missing_api_key_raises(self):
        with self.assertRaises(CharacterGenerationError):
            generate_characters(FakeBook())
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_ai.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characters.ai'`.

- [ ] **Step 3: Implement the client**

Create `backend-django/characters/ai.py`:

```python
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
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_ai.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend-django/characters/ai.py backend-django/characters/tests/test_ai.py
git commit -m "feat: add OpenRouter character generation client"
```

---

## Task 5: Persist generated characters (`characters/services.py`)

**Files:**
- Create: `backend-django/characters/services.py`
- Create: `backend-django/characters/tests/test_services.py`

- [ ] **Step 1: Write the failing test**

Create `backend-django/characters/tests/test_services.py`:

```python
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.services import store_characters


class StoreCharactersTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")

    def test_creates_characters_and_relations(self):
        data = {
            "characters": [
                {"name": "Paul Atreides", "role": "Protagonist", "description": "Heir."},
                {"name": "Lady Jessica", "role": "Mother", "description": "Bene Gesserit."},
            ],
            "relations": [
                {"from": "Paul Atreides", "to": "Lady Jessica", "label": "son"},
            ],
        }
        store_characters(self.book, data)

        self.assertEqual(Character.objects.filter(book=self.book).count(), 2)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.from_character.name, "Paul Atreides")
        self.assertEqual(rel.to_character.name, "Lady Jessica")
        self.assertEqual(rel.label, "son")
        # order is assigned by list position
        self.assertEqual(Character.objects.get(name="Paul Atreides").order, 0)

    def test_caps_at_12_characters(self):
        data = {
            "characters": [
                {"name": f"Char {i}", "role": "x", "description": "y"} for i in range(20)
            ],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 12)

    def test_skips_relations_with_unknown_endpoints(self):
        data = {
            "characters": [{"name": "Paul", "role": "x", "description": "y"}],
            "relations": [{"from": "Paul", "to": "Ghost", "label": "knows"}],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 0)

    def test_replaces_previous_characters(self):
        store_characters(
            self.book,
            {"characters": [{"name": "Old", "role": "", "description": ""}], "relations": []},
        )
        store_characters(
            self.book,
            {"characters": [{"name": "New", "role": "", "description": ""}], "relations": []},
        )
        names = list(Character.objects.filter(book=self.book).values_list("name", flat=True))
        self.assertEqual(names, ["New"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_services.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characters.services'`.

- [ ] **Step 3: Implement the service**

Create `backend-django/characters/services.py`:

```python
from django.db import transaction

from .ai import MAX_CHARACTERS
from .models import Character, CharacterRelation, unique_character_slug


@transaction.atomic
def store_characters(book, data: dict) -> None:
    """Replace all characters + relations for `book` from validated LLM `data`.

    Delete-and-replace keeps regeneration simple. Relations whose endpoints are
    not among the stored characters are skipped (the LLM occasionally references
    names it did not include).
    """
    CharacterRelation.objects.filter(book=book).delete()
    Character.objects.filter(book=book).delete()

    by_name: dict[str, Character] = {}
    for order, item in enumerate(data.get("characters", [])[:MAX_CHARACTERS]):
        name = (item.get("name") or "").strip()
        if not name:
            continue
        character = Character.objects.create(
            book=book,
            name=name,
            slug=unique_character_slug(book, name),
            role=(item.get("role") or "").strip()[:120],
            description=(item.get("description") or "").strip(),
            order=order,
        )
        by_name[name] = character

    for rel in data.get("relations", []):
        source = by_name.get((rel.get("from") or "").strip())
        target = by_name.get((rel.get("to") or "").strip())
        label = (rel.get("label") or "").strip()[:120]
        if source and target and label and source != target:
            CharacterRelation.objects.create(
                book=book, from_character=source, to_character=target, label=label
            )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_services.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add backend-django/characters/services.py backend-django/characters/tests/test_services.py
git commit -m "feat: add store_characters persistence service"
```

---

## Task 6: Celery task (`characters/tasks.py`)

**Files:**
- Create: `backend-django/characters/tasks.py`
- Create: `backend-django/characters/tests/test_tasks.py`

- [ ] **Step 1: Write the failing test**

Create `backend-django/characters/tests/test_tasks.py`:

```python
from unittest.mock import patch

from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterAnalysis
from characters.tasks import generate_characters_task


class GenerateTaskTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.analysis = CharacterAnalysis.objects.create(book=self.book)

    def test_success_stores_characters_and_marks_done(self):
        fake = {
            "characters": [{"name": "Paul", "role": "Protagonist", "description": "Heir."}],
            "relations": [],
        }
        with patch("characters.tasks.generate_characters", return_value=fake):
            generate_characters_task(self.book.id)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, CharacterAnalysis.Status.DONE)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 1)

    def test_failure_marks_failed_with_message(self):
        from characters.ai import CharacterGenerationError

        with patch(
            "characters.tasks.generate_characters",
            side_effect=CharacterGenerationError("boom"),
        ):
            generate_characters_task(self.book.id)

        self.analysis.refresh_from_db()
        self.assertEqual(self.analysis.status, CharacterAnalysis.Status.FAILED)
        self.assertIn("boom", self.analysis.error_message)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_tasks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characters.tasks'`.

- [ ] **Step 3: Implement the task**

Create `backend-django/characters/tasks.py`:

```python
from celery import shared_task
from django.conf import settings

from .ai import generate_characters
from .models import CharacterAnalysis
from .services import store_characters


@shared_task
def generate_characters_task(book_id: int) -> None:
    analysis = CharacterAnalysis.objects.select_related("book").get(book_id=book_id)
    analysis.status = CharacterAnalysis.Status.RUNNING
    analysis.error_message = ""
    analysis.save(update_fields=["status", "error_message", "updated_at"])

    try:
        data = generate_characters(analysis.book)
        store_characters(analysis.book, data)
    except Exception as exc:  # CharacterGenerationError + any unexpected failure
        analysis.status = CharacterAnalysis.Status.FAILED
        analysis.error_message = str(exc)[:2000]
        analysis.save(update_fields=["status", "error_message", "updated_at"])
        return

    analysis.status = CharacterAnalysis.Status.DONE
    analysis.model = settings.OPENROUTER_MODEL
    analysis.error_message = ""
    analysis.save(update_fields=["status", "model", "error_message", "updated_at"])
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_tasks.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add backend-django/characters/tasks.py backend-django/characters/tests/test_tasks.py
git commit -m "feat: add Celery task for character generation"
```

---

## Task 7: Serializers

**Files:**
- Create: `backend-django/characters/serializers.py`

- [ ] **Step 1: Write the serializers**

Create `backend-django/characters/serializers.py`:

```python
from rest_framework import serializers

from .models import Character


class CharacterListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Character
        fields = ["name", "slug", "role"]


class CharacterRelationSerializer(serializers.Serializer):
    to_slug = serializers.CharField(source="to_character.slug")
    to_name = serializers.CharField(source="to_character.name")
    label = serializers.CharField()


class CharacterDetailSerializer(serializers.ModelSerializer):
    relations = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = ["name", "slug", "role", "description", "relations"]

    @staticmethod
    def get_relations(obj):
        return CharacterRelationSerializer(obj.relations_from.all(), many=True).data


class CharacterListResponseSerializer(serializers.Serializer):
    status = serializers.CharField(allow_null=True)
    characters = CharacterListSerializer(many=True)
```

- [ ] **Step 2: Verify it imports**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -c "import django; django.setup(); from characters.serializers import CharacterListResponseSerializer; print('ok')"`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend-django/characters/serializers.py
git commit -m "feat: add character serializers"
```

---

## Task 8: Views, URLs, and API tests

**Files:**
- Create: `backend-django/characters/views.py`, `backend-django/characters/urls.py`
- Modify: `backend-django/config/urls.py`
- Create: `backend-django/characters/tests/test_api.py`

- [ ] **Step 1: Write the failing API test**

Create `backend-django/characters/tests/test_api.py`:

```python
from unittest.mock import patch

from rest_framework.test import APITestCase

from books.models import Book
from characters.models import Character, CharacterAnalysis
from users.models import User


class CharacterApiTests(APITestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.user = User.objects.create_user(
            email="a@example.com", handle="ann", password="passw0rd123"
        )

    def _generate_url(self):
        return f"/api/books/{self.book.slug}/characters/generate/"

    def test_generate_requires_auth(self):
        res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 401)

    def test_generate_enqueues_and_returns_pending(self):
        self.client.force_authenticate(self.user)
        with patch("characters.views.generate_characters_task.delay") as delay:
            res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "pending")
        delay.assert_called_once_with(self.book.id)

    def test_generate_is_idempotent_while_running(self):
        self.client.force_authenticate(self.user)
        CharacterAnalysis.objects.create(
            book=self.book, status=CharacterAnalysis.Status.RUNNING
        )
        with patch("characters.views.generate_characters_task.delay") as delay:
            res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "running")
        delay.assert_not_called()

    def test_list_is_public(self):
        CharacterAnalysis.objects.create(book=self.book, status=CharacterAnalysis.Status.DONE)
        Character.objects.create(book=self.book, name="Paul", slug="paul", role="Lead", order=0)
        res = self.client.get(f"/api/books/{self.book.slug}/characters/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "done")
        self.assertEqual(res.data["characters"][0]["slug"], "paul")

    def test_detail_returns_relations(self):
        paul = Character.objects.create(book=self.book, name="Paul", slug="paul", order=0)
        jess = Character.objects.create(book=self.book, name="Jessica", slug="jessica", order=1)
        from characters.models import CharacterRelation

        CharacterRelation.objects.create(
            book=self.book, from_character=paul, to_character=jess, label="son"
        )
        res = self.client.get(f"/api/books/{self.book.slug}/characters/paul/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["relations"][0]["to_slug"], "jessica")
        self.assertEqual(res.data["relations"][0]["label"], "son")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'characters.views'`.

- [ ] **Step 3: Implement the views**

Create `backend-django/characters/views.py`:

```python
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book

from .models import Character, CharacterAnalysis
from .serializers import CharacterDetailSerializer, CharacterListResponseSerializer
from .tasks import generate_characters_task

_status_response = inline_serializer(
    name="CharacterAnalysisStatus", fields={"status": serializers.CharField()}
)


class GenerateCharactersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={202: _status_response})
    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        analysis, created = CharacterAnalysis.objects.get_or_create(book=book)
        active = analysis.status in (
            CharacterAnalysis.Status.PENDING,
            CharacterAnalysis.Status.RUNNING,
        )
        # Idempotent: a pre-existing PENDING/RUNNING analysis is left alone (one job
        # per book). Otherwise (just created, or previously done/failed) re-dispatch.
        if created or not active:
            analysis.status = CharacterAnalysis.Status.PENDING
            analysis.error_message = ""
            analysis.save(update_fields=["status", "error_message", "updated_at"])
            generate_characters_task.delay(book.id)
        return Response({"status": analysis.status}, status=status.HTTP_202_ACCEPTED)


class CharacterListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CharacterListResponseSerializer)
    def get(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        analysis = CharacterAnalysis.objects.filter(book=book).first()
        characters = Character.objects.filter(book=book)
        payload = {
            "status": analysis.status if analysis else None,
            "characters": characters,
        }
        return Response(CharacterListResponseSerializer(payload).data)


class CharacterDetailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=CharacterDetailSerializer)
    def get(self, request, slug, char_slug):
        character = get_object_or_404(
            Character.objects.prefetch_related("relations_from__to_character"),
            book__slug=slug,
            slug=char_slug,
        )
        return Response(CharacterDetailSerializer(character).data)
```

- [ ] **Step 4: Implement the URLs**

Create `backend-django/characters/urls.py`:

```python
from django.urls import path

from .views import CharacterDetailView, CharacterListView, GenerateCharactersView

urlpatterns = [
    path(
        "books/<slug:slug>/characters/generate/",
        GenerateCharactersView.as_view(),
        name="character-generate",
    ),
    path(
        "books/<slug:slug>/characters/",
        CharacterListView.as_view(),
        name="character-list",
    ),
    path(
        "books/<slug:slug>/characters/<slug:char_slug>/",
        CharacterDetailView.as_view(),
        name="character-detail",
    ),
]
```

- [ ] **Step 5: Wire into the root URLconf**

In `backend-django/config/urls.py`, add an import and an include. After the `from shelf.views import PublicShelfEntryListView` line is fine for imports; add the include right after the `path("api/", include("books.urls")),` line:

```python
    path("api/", include("characters.urls")),
```

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/tests/test_api.py -v`
Expected: 5 passed.

- [ ] **Step 7: Run the whole app test suite + check**

Run: `cd backend-django && DJANGO_ENV=dev uv run python -m pytest characters/ -v && DJANGO_ENV=dev uv run python manage.py check`
Expected: all characters tests pass; check clean.

- [ ] **Step 8: Commit**

```bash
git add backend-django/characters/views.py backend-django/characters/urls.py backend-django/characters/tests/test_api.py backend-django/config/urls.py
git commit -m "feat: add character API endpoints"
```

---

## Task 9: Regenerate the OpenAPI snapshot

**Files:**
- Modify: `docs/api/openapi.yml`

- [ ] **Step 1: Regenerate**

Run: `make regenerate-openapi`
Expected: `docs/api/openapi.yml` updated with the three `/api/books/{slug}/characters/...` paths.

- [ ] **Step 2: Run the contract test**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema --noinput`
Expected: OK.

- [ ] **Step 3: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs: regenerate OpenAPI snapshot for characters"
```

---

## Task 10: Frontend types + API client

**Files:**
- Create: `svelte-frontend/src/lib/types/character.ts`
- Create: `svelte-frontend/src/lib/api/characters.ts`

- [ ] **Step 1: Write the types**

Create `svelte-frontend/src/lib/types/character.ts`:

```ts
export type CharacterAnalysisStatus = 'pending' | 'running' | 'done' | 'failed' | null;

export interface CharacterSummary {
	name: string;
	slug: string;
	role: string;
}

export interface CharacterRelation {
	to_slug: string;
	to_name: string;
	label: string;
}

export interface CharacterDetail extends CharacterSummary {
	description: string;
	relations: CharacterRelation[];
}

export interface CharacterListResponse {
	status: CharacterAnalysisStatus;
	characters: CharacterSummary[];
}
```

- [ ] **Step 2: Write the API client**

Create `svelte-frontend/src/lib/api/characters.ts`:

```ts
import { apiFetch } from './_client';
import type { CharacterDetail, CharacterListResponse } from '$lib/types/character';

/** Status + characters for one book (public). */
export function fetchCharacters(
	fetchFn: typeof fetch,
	bookSlug: string,
	isServerSide = false
) {
	return apiFetch<CharacterListResponse>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/`,
		undefined,
		isServerSide
	);
}

/** One character + its relations (public). */
export function fetchCharacter(
	fetchFn: typeof fetch,
	bookSlug: string,
	charSlug: string,
	isServerSide = false
) {
	return apiFetch<CharacterDetail>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/${encodeURIComponent(charSlug)}/`,
		undefined,
		isServerSide
	);
}

/** Enqueue generation (auth). Returns the new analysis status. */
export function generateCharacters(fetchFn: typeof fetch, bookSlug: string) {
	return apiFetch<{ status: string }>(
		fetchFn,
		`/books/${encodeURIComponent(bookSlug)}/characters/generate/`,
		{ method: 'POST' }
	);
}
```

- [ ] **Step 3: Verify types compile**

Run: `cd svelte-frontend && npm run check`
Expected: no errors from the new files (pre-existing warnings unrelated are fine).

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/types/character.ts svelte-frontend/src/lib/api/characters.ts
git commit -m "feat: add character types and api client"
```

---

## Task 11: Monogram util + CharacterCard component

**Files:**
- Create: `svelte-frontend/src/lib/utils/monogram.ts`
- Create: `svelte-frontend/src/lib/components/character/CharacterCard.svelte`

- [ ] **Step 1: Write the monogram util**

Create `svelte-frontend/src/lib/utils/monogram.ts`:

```ts
const COLORS = [
	'#3f5bd9',
	'#b94e7e',
	'#3a8f6d',
	'#cfa86d',
	'#6d4ed1',
	'#c2542f',
	'#2f8fc2',
	'#5f5f5f'
];

/** First letter of first + last word, uppercased (or first two letters). */
export function initials(name: string): string {
	const parts = name.trim().split(/\s+/).filter(Boolean);
	if (parts.length === 0) return '?';
	if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
	return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/** Deterministic colour from a name. */
export function monogramColor(name: string): string {
	let hash = 0;
	for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) >>> 0;
	return COLORS[hash % COLORS.length];
}
```

- [ ] **Step 2: Write the CharacterCard**

Create `svelte-frontend/src/lib/components/character/CharacterCard.svelte`:

```svelte
<script lang="ts">
	import type { CharacterSummary } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let { character, bookSlug }: { character: CharacterSummary; bookSlug: string } = $props();
</script>

<a
	href="/books/{bookSlug}/characters/{character.slug}"
	class="flex flex-col items-center gap-2 rounded-xl border border-rule bg-surface p-4 text-center transition-colors hover:bg-paper-2"
>
	<div
		class="flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold text-white"
		style="background:{monogramColor(character.name)}"
	>
		{initials(character.name)}
	</div>
	<div class="text-sm font-semibold leading-tight">{character.name}</div>
	{#if character.role}
		<div class="text-xs text-muted">{character.role}</div>
	{/if}
</a>
```

- [ ] **Step 3: Verify it compiles**

Run: `cd svelte-frontend && npm run check`
Expected: no new errors.

- [ ] **Step 4: Commit**

```bash
git add svelte-frontend/src/lib/utils/monogram.ts svelte-frontend/src/lib/components/character/CharacterCard.svelte
git commit -m "feat: add monogram util and CharacterCard"
```

---

## Task 12: CharacterSection + book page wiring

**Files:**
- Create: `svelte-frontend/src/lib/components/character/CharacterSection.svelte`
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.server.ts`
- Modify: `svelte-frontend/src/routes/books/[slug]/+page.svelte`

- [ ] **Step 1: Write the CharacterSection**

Create `svelte-frontend/src/lib/components/character/CharacterSection.svelte`:

```svelte
<script lang="ts">
	import { onDestroy } from 'svelte';
	import { toast } from 'svelte-sonner';
	import type {
		CharacterAnalysisStatus,
		CharacterSummary
	} from '$lib/types/character';
	import { fetchCharacters, generateCharacters } from '$lib/api/characters';
	import CharacterCard from './CharacterCard.svelte';

	let {
		bookSlug,
		initialStatus,
		initialCharacters,
		isAuthenticated
	}: {
		bookSlug: string;
		initialStatus: CharacterAnalysisStatus;
		initialCharacters: CharacterSummary[];
		isAuthenticated: boolean;
	} = $props();

	let status = $state<CharacterAnalysisStatus>(initialStatus);
	let characters = $state<CharacterSummary[]>(initialCharacters);
	let starting = $state(false);
	let pollTimer: ReturnType<typeof setTimeout> | undefined;

	const isBusy = $derived(status === 'pending' || status === 'running');

	function stopPolling() {
		if (pollTimer) clearTimeout(pollTimer);
		pollTimer = undefined;
	}

	async function poll() {
		const { data } = await fetchCharacters(fetch, bookSlug);
		if (data) {
			status = data.status;
			characters = data.characters;
		}
		if (status === 'pending' || status === 'running') {
			pollTimer = setTimeout(poll, 3000);
		}
	}

	async function startGeneration() {
		if (starting || isBusy) return;
		starting = true;
		const { data, error } = await generateCharacters(fetch, bookSlug);
		starting = false;
		if (error || !data) {
			toast.error('Could not start generation');
			return;
		}
		status = data.status as CharacterAnalysisStatus;
		stopPolling();
		pollTimer = setTimeout(poll, 3000);
	}

	onDestroy(stopPolling);
</script>

<section class="space-y-4">
	<div class="flex items-center justify-between">
		<h2 class="text-lg font-semibold">Characters</h2>
		{#if isAuthenticated && !isBusy}
			<button
				onclick={startGeneration}
				disabled={starting}
				class="rounded-md border border-rule bg-surface px-3 py-1.5 text-xs font-medium transition-colors hover:bg-paper-2 disabled:opacity-50"
			>
				{characters.length > 0 ? 'Regenerate AI' : 'Generate AI'}
			</button>
		{/if}
	</div>

	{#if isBusy}
		<p class="text-sm text-muted">Generating… this can take up to a minute.</p>
	{:else if status === 'failed' && characters.length === 0}
		<p class="text-sm text-muted">Generation failed.{isAuthenticated ? ' Try again above.' : ''}</p>
	{:else if characters.length > 0}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
			{#each characters as character (character.slug)}
				<CharacterCard {character} {bookSlug} />
			{/each}
		</div>
	{:else}
		<p class="text-sm text-muted">
			No character analysis yet.{isAuthenticated ? '' : ' Sign in to generate it.'}
		</p>
	{/if}
</section>
```

- [ ] **Step 2: Load characters server-side on the book page**

In `svelte-frontend/src/routes/books/[slug]/+page.server.ts`:

Add the import after the existing `fetchMyShelves` import:

```ts
import { fetchCharacters } from '$lib/api/characters';
```

Add a call to the `Promise.all` array (append as the last entry, and add `charactersRes` to the destructure):

```ts
	const [bookRes, ratingRes, entryRes, reviewsRes, myReviewRes, myShelvesRes, charactersRes] =
		await Promise.all([
			getBook(fetch, params.slug),
			user ? fetchUserRating(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
			user ? fetchShelfEntry(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
			fetchReviews(fetch, params.slug, 1, true),
			user ? fetchMyReview(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
			user ? fetchMyShelves(fetch, params.slug, true) : Promise.resolve({ data: null, error: null }),
			fetchCharacters(fetch, params.slug, true)
		]);
```

Add to the returned object (after `myShelves: myShelvesRes.data ?? []`):

```ts
		charactersStatus: charactersRes.data?.status ?? null,
		characters: charactersRes.data?.characters ?? []
```

(Add a comma after the `myShelves` line.)

- [ ] **Step 3: Render the section on the book page**

In `svelte-frontend/src/routes/books/[slug]/+page.svelte`:

Add the import after the `ReviewSection` import:

```ts
	import CharacterSection from '$lib/components/character/CharacterSection.svelte';
```

Insert the section between `<BookDescription ... />` and `<ReviewSection ... />`:

```svelte
				<CharacterSection
					bookSlug={data.book.slug}
					initialStatus={data.charactersStatus}
					initialCharacters={data.characters}
					isAuthenticated={!!data.user}
				/>
```

- [ ] **Step 4: Verify**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no new errors.

- [ ] **Step 5: Commit**

```bash
git add svelte-frontend/src/lib/components/character/CharacterSection.svelte svelte-frontend/src/routes/books/[slug]/+page.server.ts svelte-frontend/src/routes/books/[slug]/+page.svelte
git commit -m "feat: add character section to book page with polling"
```

---

## Task 13: RelationGraph + character subpage

**Files:**
- Create: `svelte-frontend/src/lib/components/character/RelationGraph.svelte`
- Create: `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.server.ts`
- Create: `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.svelte`

- [ ] **Step 1: Write the RelationGraph (hand-rolled ego SVG)**

Create `svelte-frontend/src/lib/components/character/RelationGraph.svelte`:

```svelte
<script lang="ts">
	import type { CharacterRelation } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let {
		centerName,
		bookSlug,
		relations
	}: { centerName: string; bookSlug: string; relations: CharacterRelation[] } = $props();

	const W = 360;
	const H = 360;
	const CX = W / 2;
	const CY = H / 2;
	const R = 130;

	// Position each related node evenly around a circle.
	const nodes = $derived(
		relations.map((rel, i) => {
			const angle = (2 * Math.PI * i) / Math.max(relations.length, 1) - Math.PI / 2;
			return {
				rel,
				x: CX + R * Math.cos(angle),
				y: CY + R * Math.sin(angle)
			};
		})
	);
</script>

{#if relations.length === 0}
	<p class="text-sm text-muted">No relations recorded.</p>
{:else}
	<svg viewBox="0 0 {W} {H}" class="w-full max-w-md rounded-xl border border-rule bg-surface">
		{#each nodes as node (node.rel.to_slug)}
			<line x1={CX} y1={CY} x2={node.x} y2={node.y} stroke="#8884" stroke-width="2" />
			<text
				x={(CX + node.x) / 2}
				y={(CY + node.y) / 2 - 4}
				fill="currentColor"
				class="text-muted"
				font-size="11"
				text-anchor="middle">{node.rel.label}</text
			>
		{/each}

		{#each nodes as node (node.rel.to_slug)}
			<a href="/books/{bookSlug}/characters/{node.rel.to_slug}">
				<circle cx={node.x} cy={node.y} r="26" fill={monogramColor(node.rel.to_name)} />
				<text x={node.x} y={node.y + 4} fill="#fff" font-size="12" text-anchor="middle"
					>{initials(node.rel.to_name)}</text
				>
			</a>
		{/each}

		<circle cx={CX} cy={CY} r="32" fill={monogramColor(centerName)} stroke="#fff" stroke-width="3" />
		<text x={CX} y={CY + 5} fill="#fff" font-size="14" font-weight="bold" text-anchor="middle"
			>{initials(centerName)}</text
		>
	</svg>
{/if}
```

- [ ] **Step 2: Write the subpage loader**

Create `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.server.ts`:

```ts
import { error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { fetchCharacter } from '$lib/api/characters';

export const load: PageServerLoad = async ({ fetch, params }) => {
	const { data, error: err } = await fetchCharacter(fetch, params.slug, params.charSlug, true);
	if (err || !data) {
		throw error(err?.status || 404, err?.detail || 'Character not found');
	}
	return { character: data, bookSlug: params.slug };
};
```

- [ ] **Step 3: Write the subpage**

Create `svelte-frontend/src/routes/books/[slug]/characters/[charSlug]/+page.svelte`:

```svelte
<script lang="ts">
	import type { PageProps } from './$types';
	import RelationGraph from '$lib/components/character/RelationGraph.svelte';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let { data }: PageProps = $props();
	let character = $derived(data.character);
</script>

<svelte:head>
	<title>{character.name} — Storyshelf</title>
</svelte:head>

<div class="mx-auto max-w-[900px] space-y-8 px-6 py-8 md:px-10">
	<a href="/books/{data.bookSlug}" class="text-sm text-info hover:underline">← Back to book</a>

	<div class="flex items-center gap-4">
		<div
			class="flex h-16 w-16 items-center justify-center rounded-full text-2xl font-bold text-white"
			style="background:{monogramColor(character.name)}"
		>
			{initials(character.name)}
		</div>
		<div>
			<h1 class="text-2xl font-bold">{character.name}</h1>
			{#if character.role}<p class="text-muted">{character.role}</p>{/if}
		</div>
	</div>

	{#if character.description}
		<p class="leading-relaxed">{character.description}</p>
	{/if}

	<section class="space-y-3">
		<h2 class="text-lg font-semibold">Relations</h2>
		<RelationGraph
			centerName={character.name}
			bookSlug={data.bookSlug}
			relations={character.relations}
		/>
	</section>
</div>
```

- [ ] **Step 4: Verify**

Run: `cd svelte-frontend && npm run check && npm run lint`
Expected: no new errors.

- [ ] **Step 5: Commit**

```bash
git add svelte-frontend/src/lib/components/character/RelationGraph.svelte "svelte-frontend/src/routes/books/[slug]/characters"
git commit -m "feat: add character subpage with relation graph"
```

---

## Task 14: Manual end-to-end smoke (real stack)

**Files:** none (verification only)

- [ ] **Step 1: Build and start the dev stack**

Run: `make dev-build && make dev-up`
Expected: `db`, `redis`, `django`, `celery`, `svelte` all start.

- [ ] **Step 2: Apply migrations on the live dev DB**

Run: `docker exec storyshelf-django python manage.py migrate`
Expected: `characters.0001_initial ... OK`. (Per project memory: containers reload code but not schema — migrate the live DB or generation returns 500.)

- [ ] **Step 3: Confirm the worker is connected**

Run: `docker logs storyshelf-celery --tail 20`
Expected: `celery@... ready.` and a connection to `redis://redis:6379/0`.

- [ ] **Step 4: Smoke the flow**

With `OPENROUTER_API_KEY` set in `infra/.env`, open a seeded book at `http://localhost:5174/books/<slug>`, sign in, click **Generate AI**, watch it flip to “Generating…”, then cards appear. Click a card → subpage with ego-graph; click a node → that character’s page.

If `OPENROUTER_API_KEY` is empty: the section flips to “Generation failed” (expected — verifies the failure path without spending credits).

- [ ] **Step 5: Tear down (optional)**

Run: `make dev-down`

---

## Task 15: Docs — ADR-003, ARCHITECTURE, ROADMAP

**Files:**
- Create: `docs/decisions/ADR-003-celery-redis-llm.md`
- Modify: `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`

- [ ] **Step 1: Write ADR-003**

Create `docs/decisions/ADR-003-celery-redis-llm.md`:

```markdown
# ADR-003 — Celery + Redis i zewnętrzny provider LLM (OpenRouter)

> Status: Accepted · Data: 2026-06-05 · Kontekst: M13 AI Character Analysis

## Kontekst

M13 dodaje generację „kart postaci" przez LLM. Jeden call generuje do 12 postaci
+ relacje (15–40 s). Każdy zalogowany user może kliknąć „Generate AI".

## Decyzja

- **Asynchronicznie, nie synchronicznie.** Synchroniczny call blokowałby worker
  webowy na czas generacji — przy wielu równoległych klikach (np. 100) pula
  workerów się wyczerpuje i cała aplikacja przestaje odpowiadać (worker starvation).
- **Celery + Redis** jako kolejka zadań (Redis = broker + result backend). RabbitMQ
  odrzucone jako przerost — niski wolumen, brak potrzeby zaawansowanego routingu.
- **OpenRouter** jako provider (model konfigurowalny przez `OPENROUTER_MODEL`),
  wołany gołym `urllib` (spójnie z `import_books`). Bez LangChain — to jeden
  structured-output call, framework orkiestracji byłby zbędną zależnością.
- **Idempotencja per książka** + bounded worker concurrency jako bezpieczniki:
  jeden job na książkę naraz; do OpenRoutera leci max `CELERY_WORKER_CONCURRENCY`.

## Konsekwencje

- +2 elementy infry: kontener `redis` i proces `celery` worker (ten sam obraz django).
- Otwarcie fazy AI projektu — wcześniej „bez AI/Celery" było **odłożone**, nie zakazane.
- **Znane ryzyko (świadomy dług):** „każdy user + regeneracja dozwolona" = otwarta
  furtka kosztowa. Rate-limit/throttle generacji odłożony na później.
- Testy: `CELERY_TASK_ALWAYS_EAGER=True` — taski wykonują się synchronicznie, bez workera.
```

- [ ] **Step 2: Update ARCHITECTURE.md**

In `docs/ARCHITECTURE.md`:

- In the "Kontenery" section, change the container line to include redis + celery:
  `svelte → django → db (PostgreSQL)` plus `redis (broker) → celery worker`.
- Add a row to the "Django apps" table:
  `| `characters/` | Karty postaci generowane przez LLM (OpenRouter) async (Celery): `CharacterAnalysis` (status), `Character`, `CharacterRelation`; publiczny odczyt, generacja auth |`
- Add to the "API surface" block:
  ```
  /api/books/{slug}/characters/            lista + status analizy (publiczny)
  /api/books/{slug}/characters/generate/   enqueue generacji (auth, 202)
  /api/books/{slug}/characters/{char_slug}/ postać + relacje (publiczny)
  ```

- [ ] **Step 3: Update ROADMAP.md**

In `docs/ROADMAP.md`, move M13 into "Zrobione" (or mark in progress on this branch). Add a row to the "Zrobione" table:

```
| M13 AI Character Analysis | app `characters/` (Celery+Redis, OpenRouter); sekcja postaci pod książką (karty monogram), podstrona postaci + ego-graf relacji; `POST .../generate/` async, publiczny odczyt; ADR-003 | ✅ na gałęzi `feat/m13-ai-characters` |
```

Update the "Aktualny krok" / "Czego NIE robimy" notes: AI nie jest już całkowicie wykluczone — M13 świadomie otworzyło fazę AI (patrz ADR-003); pozostałe pozycje AI z „Kiedyś" dalej poza zakresem.

- [ ] **Step 4: Commit**

```bash
git add docs/decisions/ADR-003-celery-redis-llm.md docs/ARCHITECTURE.md docs/ROADMAP.md
git commit -m "docs: ADR-003 + architecture/roadmap for M13"
```

---

## Task 16: Full verification

**Files:** none

- [ ] **Step 1: Run the full CI-equivalent suite**

Run: `make verify`
Expected: ruff clean, `manage.py check` clean, pytest green (incl. all `characters/` tests), OpenAPI contract test OK, `npm run check` and `npm run lint` clean.

- [ ] **Step 2: Remove the spec + plan (per branch workflow)**

Per the project commit convention (commit 2 = remove spec/plan), do this only when the user confirms the work is approved for squash. Leave in place until then.

---

## Self-Review

**Spec coverage:**
- Monogram cards → Task 11 (util + CharacterCard). ✓
- Ego-graph, clickable nodes → Task 13 (RelationGraph `<a>` nodes). ✓
- Generate button, any logged-in user → Task 8 (`IsAuthenticated`) + Task 12 (button). ✓
- Regeneration allowed → Task 8 (`created or not active` re-dispatch) + Task 12 ("Regenerate AI"). ✓
- Max 12 → Task 5 (`[:MAX_CHARACTERS]`) + `MAX_CHARACTERS=12` in Task 4. ✓
- OpenRouter, env model, urllib, no LangChain → Task 1 (settings) + Task 4 (client). ✓
- Async, no sync → Task 6 (Celery task) + Task 8 (enqueue). ✓
- Celery + Redis, idempotent per book, bounded concurrency → Task 1/2 (infra) + Task 8 (idempotency). ✓
- Public read, auth generate → Task 8 (`AllowAny` GET, `IsAuthenticated` POST). ✓
- Endpoints (3) → Task 8 (urls). ✓
- Frontend section/subpage/polling → Tasks 12, 13. ✓
- Tests (mock urlopen, eager Celery, idempotency, gating, public read) → Tasks 4, 5, 6, 8. ✓
- OpenAPI snapshot → Task 9. ✓
- ADR-003 + docs → Task 15. ✓
- Known cost risk documented → Task 15 (ADR). ✓

**Placeholder scan:** No TBD/TODO; every code step shows full code. ✓

**Type consistency:** `CharacterListResponseSerializer{status, characters}` matches frontend `CharacterListResponse`. `generate_characters_task(book_id)` called identically in Task 6 test and Task 8 view. `MAX_CHARACTERS` defined in `ai.py` (Task 4), imported in `services.py` (Task 5). `CharacterDetailSerializer` relations shape `{to_slug,to_name,label}` matches frontend `CharacterRelation`. ✓

**Idempotency note:** The Task 8 test `test_generate_is_idempotent_while_running` passes because a pre-existing RUNNING analysis is `active` and `created is False`, so the view does not re-dispatch.
