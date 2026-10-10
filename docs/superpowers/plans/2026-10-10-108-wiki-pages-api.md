# Wiki Pages API Implementation Plan (#108)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Django `wiki` app stores each user's OKF Pages in Postgres, validates every save (frontmatter, `type`, Template headings), keeps every change as a Version, rejects stale edits with 409, and seeds the Wiedźmin + Solaris demo Pages.

**Architecture:** `wiki/okf.py` holds pure OKF functions (parse, validate, slugify, Path, Template) with no DB or DRF. `wiki/services.py` owns writes: `insert_page`, `create_page`, `edit_page` (transactions, Versions, `select_for_update` + `base_version` check). DRF views in `wiki/views.py` only parse input, call services and map exceptions to 400/409. `manage.py seed <email>` reuses `insert_page`.

**Tech Stack:** Django 6, DRF, drf-spectacular, PyYAML (`yaml.safe_load` / `safe_dump`), Postgres 16, pytest + pytest-django (Django `TestCase` / `APITestCase` classes).

**Spec:** `docs/superpowers/specs/2026-10-10-108-wiki-pages-api.md`

## Global Constraints

- No new dependencies except declaring `pyyaml` explicitly (already in `uv.lock` 6.0.3 as a transitive dep)
- Template headings and error messages are verbatim from `frontend/src/wiki.ts` (`TEMPLATES`, `validateEdit`): `Invalid frontmatter: Missing frontmatter`, `Invalid frontmatter: not a mapping`, `Missing type`, `Page type can't change`, `Missing title`, `Missing template headings: A, B`, `Page already exists: <path>`
- Edit stores `content` byte for byte (no YAML re-dump, no whitespace trimming); `yaml.safe_dump` only when rendering an empty Template
- Every wiki view: `permission_classes = (permissions.IsAuthenticated,)`; queryset filtered by `owner=request.user` → other users' Pages are 404
- Path in URLs has no leading `/` and matches `(books|characters|places|universes)/[a-z0-9-]+\.md`
- Python code: ruff `E, F, I, N`, line length 100; English comments, short
- Backend commands run from `backend-django/`. Tests need the dev DB (`books-db` container on :5432) and the env file: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest <target> -q`
- Commit titles ≤ 50 chars, conventional commits ending `[#108]`, no `Co-Authored-By`; one simple git command per call (worktree guard)

## Review Focus

1. Stale edit really changes nothing: 409 leaves `Page.content` and the Version count untouched (Task 3, `test_stale_base_version_returns_409_and_changes_nothing`)
2. Content round-trip: an edit with trailing whitespace and an extra section is stored exactly (Task 3, `test_edit_stores_content_byte_for_byte`)
3. Title with YAML-special characters (`Diuna: Mesjasz`) renders valid frontmatter and a clean slug (Task 2)
4. Owner scoping on all three detail routes (GET, PUT, versions) → 404 (Task 3)

## File Map

```
backend-django/
  pyproject.toml, uv.lock                 + pyyaml                          (Task 1)
  config/settings/base.py                 + "wiki.apps.WikiConfig"           (Task 1)
  config/urls.py                          + path("api/wiki/", ...)           (Task 3)
  wiki/__init__.py, apps.py, admin.py                                        (Task 1)
  wiki/models.py                          Page, PageVersion                  (Task 1)
  wiki/migrations/0001_initial.py         generated                          (Task 1)
  wiki/okf.py                             pure OKF functions                 (Task 2)
  wiki/services.py                        insert/create/edit                 (Task 3)
  wiki/serializers.py, views.py, urls.py  HTTP layer                         (Task 3)
  wiki/management/commands/seed.py                                           (Task 4)
  wiki/fixtures/{books,characters,places,universes}/*.md   copy of 15 files  (Task 4)
  wiki/tests/test_okf.py, test_pages_api.py, test_seed.py
docs/api/openapi.yml                      regenerated                        (Task 5)
docs/ARCHITECTURE.md                      + one line on current Version      (Task 5)
```

---

### Task 0: Environment (once per worktree)

`infra/.env` is gitignored, so a fresh worktree has none. Skip if `backend-django/../infra/.env` already contains `DATABASE_URL`.

- [ ] **Step 1: Copy the env file** (from the worktree root)

```bash
cp /home/dv6/GitHub/storyshelf/infra/.env infra/.env
```

- [ ] **Step 2: Append DATABASE_URL** (uv expands `${...}` from the same file)

```bash
echo 'DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}' >> infra/.env
```

- [ ] **Step 3: Check the DB is reachable** (from `backend-django/`)

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest users/tests/test_user_me.py -q`
Expected: `15 passed`. If connection errors: `make dev-up` from the main checkout.

---

### Task 1: `wiki` app and models

**Files:**
- Create: `backend-django/wiki/__init__.py` (empty), `wiki/apps.py`, `wiki/admin.py`, `wiki/models.py`, `wiki/tests/__init__.py` (empty)
- Create (generated): `backend-django/wiki/migrations/__init__.py`, `wiki/migrations/0001_initial.py`
- Modify: `backend-django/config/settings/base.py:27` (INSTALLED_APPS), `backend-django/pyproject.toml`, `backend-django/uv.lock`

No test in this task: the models carry no logic; the `(owner, path)` constraint is covered by the 409 test in Task 3.

- [ ] **Step 1: Declare PyYAML**

Run (from `backend-django/`): `uv add pyyaml`
Expected: `pyproject.toml` dependencies gain `"pyyaml>=6.0.3"`; `uv.lock` updates.

- [ ] **Step 2: Create `wiki/apps.py`**

```python
from django.apps import AppConfig


class WikiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wiki"
```

- [ ] **Step 3: Create `wiki/models.py`**

```python
from django.conf import settings
from django.db import models


class Page(models.Model):
    """One OKF document; `content` is the source of truth, other fields are copies for queries."""

    class Type(models.TextChoices):
        BOOK = "book"
        CHARACTER = "character"
        PLACE = "place"
        UNIVERSE = "universe"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pages"
    )
    path = models.TextField()  # '/books/solaris.md', identity within one Wiki
    type = models.CharField(max_length=16, choices=Type.choices)
    title = models.TextField()
    book = models.TextField(null=True, blank=True)
    universe = models.TextField(null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["path"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "path"], name="unique_page_path_per_owner"),
        ]

    def __str__(self):
        return self.path

    @property
    def version(self):
        """Id of the newest PageVersion, the current Version (no separate pointer)."""
        return self.versions.values_list("id", flat=True).first()


class PageVersion(models.Model):
    class Kind(models.TextChoices):
        CREATED = "created"
        GENERATION = "generation"
        PROPOSAL = "proposal"
        EDIT = "edit"

    class Author(models.TextChoices):
        HUMAN = "human"
        AGENT = "agent"

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="versions")
    content = models.TextField()
    kind = models.CharField(max_length=16, choices=Kind.choices)
    author = models.CharField(max_length=8, choices=Author.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
```

- [ ] **Step 4: Create `wiki/admin.py`**

```python
from django.contrib import admin

from wiki.models import Page, PageVersion

admin.site.register(Page)
admin.site.register(PageVersion)
```

- [ ] **Step 5: Register the app** in `config/settings/base.py`, after `"users.apps.UsersConfig",`:

```python
    "users.apps.UsersConfig",
    "wiki.apps.WikiConfig",
]
```

- [ ] **Step 6: Create empty `wiki/__init__.py` and `wiki/tests/__init__.py`**

- [ ] **Step 7: Generate the migration**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python manage.py makemigrations wiki`
Expected: `wiki/migrations/0001_initial.py` with `Create model Page`, `Create model PageVersion`, `Create constraint unique_page_path_per_owner`.

- [ ] **Step 8: Check**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python manage.py check` → `System check identified no issues`
Run: `uv run ruff check .` → `All checks passed!`

- [ ] **Step 9: Commit**

```bash
git add backend-django/wiki backend-django/config/settings/base.py backend-django/pyproject.toml backend-django/uv.lock
```
```bash
git commit -m "feat: add wiki Page and PageVersion models [#108]"
```

---

### Task 2: OKF parsing, validation and Templates (`wiki/okf.py`)

**Files:**
- Create: `backend-django/wiki/okf.py`
- Test: `backend-django/wiki/tests/test_okf.py`

- [ ] **Step 1: Write the failing tests** — `wiki/tests/test_okf.py`

```python
from django.test import SimpleTestCase

from wiki import okf

BOOK = (
    "---\ntype: book\ntitle: Solaris\n---\n\n"
    "## Streszczenie\n\n## Postacie\n\n## Miejsca\n\n## Wątki i motywy\n"
)


class ValidateTest(SimpleTestCase):
    def assert_error(self, content, page_type, message, field="content"):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.validate(content, page_type)
        self.assertEqual(str(ctx.exception), message)
        self.assertEqual(ctx.exception.field, field)

    def test_valid_book_returns_frontmatter(self):
        self.assertEqual(okf.validate(BOOK, "book"), {"type": "book", "title": "Solaris"})

    def test_crlf_line_endings_are_valid(self):
        okf.validate(BOOK.replace("\n", "\r\n"), "book")

    def test_extra_sections_are_allowed(self):
        okf.validate(BOOK + "\n## Ciekawostki\n\nTekst.\n", "book")

    def test_missing_frontmatter(self):
        self.assert_error("## Streszczenie\n", "book", "Invalid frontmatter: Missing frontmatter")

    def test_broken_yaml(self):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.validate("---\ntype: [book\n---\n", "book")
        self.assertTrue(str(ctx.exception).startswith("Invalid frontmatter: "))

    def test_frontmatter_not_a_mapping(self):
        self.assert_error("---\n- a\n---\n", "book", "Invalid frontmatter: not a mapping")

    def test_missing_type(self):
        self.assert_error(BOOK.replace("type: book\n", ""), "book", "Missing type")

    def test_type_must_match_page(self):
        self.assert_error(BOOK, "character", "Page type can't change")

    def test_missing_title(self):
        self.assert_error(BOOK.replace("title: Solaris\n", ""), "book", "Missing title")

    def test_blank_title(self):
        self.assert_error(BOOK.replace("title: Solaris", "title: ' '"), "book", "Missing title")

    def test_missing_template_headings_are_listed_in_template_order(self):
        content = BOOK.replace("## Postacie\n", "").replace("## Miejsca\n", "")
        self.assert_error(content, "book", "Missing template headings: Postacie, Miejsca")


class PathTest(SimpleTestCase):
    def test_slugify(self):
        self.assertEqual(okf.slugify("Krew elfów"), "krew-elfow")
        self.assertEqual(okf.slugify("Łódź"), "lodz")
        self.assertEqual(okf.slugify("Diuna: Mesjasz"), "diuna-mesjasz")
        self.assertEqual(okf.slugify(" -Ostatnie życzenie!- "), "ostatnie-zyczenie")

    def test_page_path_per_type(self):
        self.assertEqual(okf.page_path("book", "Krew elfów"), "/books/krew-elfow.md")
        self.assertEqual(okf.page_path("universe", "Wiedźmin"), "/universes/wiedzmin.md")
        self.assertEqual(
            okf.page_path("character", "Geralt", "/books/krew-elfow.md"),
            "/characters/geralt--krew-elfow.md",
        )
        self.assertEqual(
            okf.page_path("place", "Kaer Morhen", "/books/krew-elfow.md"),
            "/places/kaer-morhen--krew-elfow.md",
        )

    def test_title_without_letters_or_digits_is_rejected(self):
        with self.assertRaises(okf.OKFError) as ctx:
            okf.page_path("book", "!!!")
        self.assertEqual(ctx.exception.field, "title")


class RenderTemplateTest(SimpleTestCase):
    def test_every_template_passes_validation(self):
        for page_type in okf.TEMPLATES:
            with self.subTest(page_type=page_type):
                content = okf.render_template(page_type, {"title": "X"})
                okf.validate(content, page_type)

    def test_book_template_frontmatter(self):
        content = okf.render_template(
            "book", {"title": "Diuna: Mesjasz", "author": "Frank Herbert", "year": 1969,
                     "universe": None},
        )
        frontmatter, body = okf.parse(content)
        self.assertEqual(frontmatter, {
            "type": "book", "title": "Diuna: Mesjasz", "author": "Frank Herbert", "year": 1969,
            "status": "draft",
        })
        self.assertTrue(body.startswith("## Streszczenie\n"))
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_okf.py -q`
Expected: collection error `ImportError: cannot import name 'okf' from 'wiki'`.

- [ ] **Step 3: Implement `wiki/okf.py`**

```python
"""OKF v0.2 Pages: parsing, validation, Paths and empty Templates. No DB, no DRF."""

import re
import unicodedata

import yaml

DIRS = {"book": "books", "character": "characters", "place": "places", "universe": "universes"}

# Szablon: `##` headings every Page of a type must keep (same as frontend/src/wiki.ts)
TEMPLATES = {
    "book": ["Streszczenie", "Postacie", "Miejsca", "Wątki i motywy"],
    "character": ["Opis", "Rola w książce", "Powiązania"],
    "place": ["Opis", "Rola w książce"],
    "universe": ["Opis"],
}

# Opening `---`, optional YAML block, closing `---`; LF or CRLF
FRONTMATTER = re.compile(r"^---\r?\n(?:([\s\S]*?)\r?\n)?---(?:\r?\n|$)")


class OKFError(ValueError):
    """Message for the User; `field` is the API error key."""

    def __init__(self, message, field="content"):
        super().__init__(message)
        self.field = field


def parse(content):
    match = FRONTMATTER.match(content)
    if not match:
        raise OKFError("Invalid frontmatter: Missing frontmatter")
    try:
        frontmatter = yaml.safe_load(match[1] or "")
    except yaml.YAMLError as e:
        raise OKFError(f"Invalid frontmatter: {getattr(e, 'problem', None) or e}") from e
    if frontmatter is None:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        raise OKFError("Invalid frontmatter: not a mapping")
    return frontmatter, content[match.end():].lstrip()


def validate(content, page_type):
    """Frontmatter of a valid Page, or OKFError with the first problem."""
    frontmatter, body = parse(content)
    if "type" not in frontmatter:
        raise OKFError("Missing type")
    # type picks the Path directory, so changing it would break the Page identity
    if frontmatter["type"] != page_type:
        raise OKFError("Page type can't change")
    title = frontmatter.get("title")
    if not isinstance(title, str) or not title.strip():
        raise OKFError("Missing title")
    lines = {line.strip() for line in body.splitlines()}
    missing = [h for h in TEMPLATES[page_type] if f"## {h}" not in lines]
    if missing:
        raise OKFError(f"Missing template headings: {', '.join(missing)}")
    return frontmatter


def slugify(text):
    """ASCII slug for Paths; 'Krew elfów' → 'krew-elfow' (same rules as wiki.ts)."""
    text = unicodedata.normalize("NFD", text.replace("ł", "l").replace("Ł", "L"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def page_path(page_type, title, book=None):
    """Characters and places are per book for now: '/characters/geralt--krew-elfow.md'."""
    slug = slugify(title)
    if not slug:
        raise OKFError("Title needs at least one letter or digit", field="title")
    if page_type in ("character", "place"):
        slug = f"{slug}--{book.removeprefix('/books/').removesuffix('.md')}"
    return f"/{DIRS[page_type]}/{slug}.md"


def render_template(page_type, meta):
    """Empty Page: frontmatter with `status: draft`, then the Template headings."""
    fields = {"type": page_type, **{k: v for k, v in meta.items() if v is not None}}
    fields["status"] = "draft"
    frontmatter = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False)
    body = "\n".join(f"## {h}\n" for h in TEMPLATES[page_type])
    return f"---\n{frontmatter}---\n\n{body}"
```

- [ ] **Step 4: Run the tests**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_okf.py -q`
Expected: `16 passed`.

- [ ] **Step 5: Lint**

Run: `uv run ruff check .` → `All checks passed!`

- [ ] **Step 6: Commit**

```bash
git add backend-django/wiki/okf.py backend-django/wiki/tests/test_okf.py
```
```bash
git commit -m "feat: add OKF validation and templates [#108]"
```

---

### Task 3: Services and Pages API

**Files:**
- Create: `backend-django/wiki/services.py`, `wiki/serializers.py`, `wiki/views.py`, `wiki/urls.py`
- Modify: `backend-django/config/urls.py:12` (after the `api/u/` line)
- Test: `backend-django/wiki/tests/test_pages_api.py`

- [ ] **Step 1: Write the failing tests** — `wiki/tests/test_pages_api.py`

```python
from rest_framework import status
from rest_framework.test import APITestCase

from config.test_helpers import AuthTestHelper
from users.models import User
from wiki import services
from wiki.models import Page

URL = "/api/wiki/pages/"
SOLARIS = f"{URL}books/solaris.md"


class PagesAPITest(AuthTestHelper, APITestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()
        cls.other = User.objects.create_user(
            email="other@test.com", handle="other", password="password123"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def create(self, **data):
        return self.client.post(URL, data, format="json")

    def edit(self, url, content, base_version):
        return self.client.put(
            url, {"content": content, "base_version": base_version}, format="json"
        )

    # Create

    def test_create_book_returns_template_page_with_created_version(self):
        resp = self.create(type="book", title="Solaris", author="Stanisław Lem", year=1961)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["path"], "/books/solaris.md")
        self.assertIn("status: draft", resp.data["content"])
        self.assertIn("## Wątki i motywy", resp.data["content"])
        page = Page.objects.get(owner=self.user, path="/books/solaris.md")
        version = page.versions.get()
        self.assertEqual((version.kind, version.author), ("created", "human"))
        self.assertEqual(resp.data["version"], version.id)

    def test_create_slugs_polish_title(self):
        resp = self.create(type="book", title="Krew elfów")
        self.assertEqual(resp.data["path"], "/books/krew-elfow.md")

    def test_create_without_type_returns_400_on_type(self):
        resp = self.create(title="Solaris")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", resp.data)

    def test_create_with_unknown_type_returns_400_on_type(self):
        resp = self.create(type="author", title="Lem")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("type", resp.data)

    def test_create_existing_path_returns_409(self):
        self.create(type="book", title="Solaris")
        resp = self.create(type="book", title="Solaris")
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp.data["detail"], "Page already exists: /books/solaris.md")
        self.assertEqual(Page.objects.filter(owner=self.user).count(), 1)

    def test_create_character_needs_existing_book(self):
        resp = self.create(type="character", title="Snaut", book="/books/solaris.md")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", resp.data)
        self.create(type="book", title="Solaris")
        resp = self.create(type="character", title="Snaut", book="/books/solaris.md")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["path"], "/characters/snaut--solaris.md")
        self.assertEqual(resp.data["book"], "/books/solaris.md")

    def test_create_character_without_book_returns_400(self):
        resp = self.create(type="character", title="Snaut")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", resp.data)

    def test_create_book_with_unknown_universe_returns_400(self):
        resp = self.create(type="book", title="Krew elfów", universe="/universes/wiedzmin.md")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("universe", resp.data)

    # List and read

    def test_list_filters_by_type_and_hides_content(self):
        self.create(type="book", title="Solaris")
        self.create(type="universe", title="Wiedźmin")
        services.create_page(self.other, "book", "Lalka")
        resp = self.client.get(URL, {"type": "book"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([p["path"] for p in resp.data], ["/books/solaris.md"])
        self.assertNotIn("content", resp.data[0])
        self.assertEqual(len(self.client.get(URL).data), 2)

    def test_get_page_returns_content_and_version(self):
        created = self.create(type="book", title="Solaris").data
        resp = self.client.get(SOLARIS)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["content"], created["content"])
        self.assertEqual(resp.data["version"], created["version"])

    # Edit and versions

    def test_edit_adds_version_and_updates_title_but_not_path(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"].replace("title: Solaris", "title: Solaris (1961)")
        resp = self.edit(SOLARIS, content, page["version"])
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["title"], "Solaris (1961)")
        self.assertEqual(resp.data["path"], "/books/solaris.md")
        self.assertNotEqual(resp.data["version"], page["version"])
        versions = self.client.get(f"{SOLARIS}/versions/").data
        self.assertEqual(versions["total"], 2)
        self.assertEqual([v["kind"] for v in versions["data"]], ["edit", "created"])

    def test_edit_stores_content_byte_for_byte(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"] + "\n## Ciekawostki\n\n  "
        self.edit(SOLARIS, content, page["version"])
        self.assertEqual(Page.objects.get(owner=self.user).content, content)

    def test_edit_without_template_heading_returns_400(self):
        page = self.create(type="book", title="Solaris").data
        resp = self.edit(SOLARIS, page["content"].replace("## Postacie\n", ""), page["version"])
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data, {"content": ["Missing template headings: Postacie"]})
        self.assertEqual(Page.objects.get(owner=self.user).versions.count(), 1)

    def test_edit_changing_type_returns_400(self):
        page = self.create(type="book", title="Solaris").data
        content = page["content"].replace("type: book", "type: universe")
        resp = self.edit(SOLARIS, content, page["version"])
        self.assertEqual(resp.data, {"content": ["Page type can't change"]})

    def test_stale_base_version_returns_409_and_changes_nothing(self):
        page = self.create(type="book", title="Solaris").data
        first = page["content"] + "\nPierwsza zmiana.\n"
        self.edit(SOLARIS, first, page["version"])
        resp = self.edit(SOLARIS, page["content"] + "\nDruga zmiana.\n", page["version"])
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        stored = Page.objects.get(owner=self.user)
        self.assertEqual(stored.content, first)
        self.assertEqual(stored.versions.count(), 2)

    # Access

    def test_other_users_page_returns_404(self):
        services.create_page(self.other, "book", "Lalka")
        url = f"{URL}books/lalka.md"
        self.assertEqual(self.client.get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.edit(url, "x", 1).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.get(f"{url}/versions/").status_code, status.HTTP_404_NOT_FOUND
        )

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_pages_api.py -q`
Expected: collection error `ImportError: cannot import name 'services' from 'wiki'`.

- [ ] **Step 3: Implement `wiki/services.py`**

```python
"""Writes to Pages. Every change goes through here (API now, Agent in M3)."""

from django.db import IntegrityError, transaction

from wiki import okf
from wiki.models import Page, PageVersion


class PathTaken(Exception):
    pass


class StaleVersion(Exception):
    pass


def _str_or_none(value):
    return value if isinstance(value, str) else None


def _apply(page, content, frontmatter):
    """Content plus the frontmatter copies used by queries."""
    page.content = content
    page.title = frontmatter["title"]
    page.book = _str_or_none(frontmatter.get("book"))
    page.universe = _str_or_none(frontmatter.get("universe"))


def insert_page(owner, path, page_type, content):
    """New Page with its first Version (`created`, `human`)."""
    frontmatter = okf.validate(content, page_type)
    page = Page(owner=owner, path=path, type=page_type)
    _apply(page, content, frontmatter)
    try:
        with transaction.atomic():
            page.save()
            PageVersion.objects.create(page=page, content=content, kind="created", author="human")
    except IntegrityError as e:
        raise PathTaken(f"Page already exists: {path}") from e
    return page


def _check_ref(owner, path, page_type):
    if not Page.objects.filter(owner=owner, path=path, type=page_type).exists():
        raise okf.OKFError(f"No {page_type} page at {path}", field=page_type)


def create_page(owner, page_type, title, *, author=None, year=None, book=None, universe=None):
    """Empty Template Page; the server picks the Path."""
    if page_type in ("character", "place"):
        if not book:
            raise okf.OKFError("This field is required.", field="book")
        _check_ref(owner, book, "book")
        meta = {"title": title, "book": book}
    elif page_type == "book":
        if universe:
            _check_ref(owner, universe, "universe")
        meta = {"title": title, "author": author, "year": year, "universe": universe}
    else:
        meta = {"title": title}
    path = okf.page_path(page_type, title, book)
    return insert_page(owner, path, page_type, okf.render_template(page_type, meta))


def edit_page(page, content, base_version, *, kind="edit", author="human"):
    """New Version on top of `base_version`; StaleVersion if the Page moved on."""
    frontmatter = okf.validate(content, page.type)
    with transaction.atomic():
        locked = Page.objects.select_for_update().get(pk=page.pk)
        if locked.version != base_version:
            raise StaleVersion("Page has a newer version, reload it")
        _apply(locked, content, frontmatter)
        locked.save()
        PageVersion.objects.create(page=locked, content=content, kind=kind, author=author)
    return locked
```

- [ ] **Step 4: Implement `wiki/serializers.py`**

```python
from rest_framework import serializers

from wiki.models import Page, PageVersion


class PageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["path", "type", "title", "book", "universe"]


class PageSerializer(serializers.ModelSerializer):
    version = serializers.IntegerField(read_only=True)

    class Meta:
        model = Page
        fields = ["path", "type", "title", "book", "universe", "content", "version"]


class PageCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Page.Type.choices)
    title = serializers.CharField(max_length=200)
    author = serializers.CharField(max_length=200, required=False)
    year = serializers.IntegerField(required=False)
    book = serializers.CharField(required=False)
    universe = serializers.CharField(required=False)


class PageEditSerializer(serializers.Serializer):
    # Stored byte for byte, so no trimming
    content = serializers.CharField(trim_whitespace=False)
    base_version = serializers.IntegerField()


class PageVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageVersion
        fields = ["id", "kind", "author", "content", "created_at"]
```

- [ ] **Step 5: Implement `wiki/views.py`**

```python
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response

from wiki import okf, services
from wiki.models import Page, PageVersion
from wiki.serializers import (
    PageCreateSerializer,
    PageEditSerializer,
    PageListSerializer,
    PageSerializer,
    PageVersionSerializer,
)

INVALID = OpenApiResponse(description="Invalid input or OKF content")
CONFLICT = OpenApiResponse(description="Path taken or stale base_version")


def get_own_page(request, path):
    """Other users' Pages are 404, not 403."""
    return get_object_or_404(Page, owner=request.user, path=f"/{path}")


class PageListCreateView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        parameters=[OpenApiParameter("type", enum=Page.Type.values)],
        responses=PageListSerializer(many=True),
    )
    def get(self, request):
        pages = Page.objects.filter(owner=request.user)
        if page_type := request.query_params.get("type"):
            pages = pages.filter(type=page_type)
        return Response(PageListSerializer(pages, many=True).data)

    @extend_schema(
        request=PageCreateSerializer,
        responses={201: PageSerializer, 400: INVALID, 409: CONFLICT},
    )
    def post(self, request):
        serializer = PageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        try:
            page = services.create_page(request.user, data.pop("type"), **data)
        except okf.OKFError as e:
            return Response({e.field: [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except services.PathTaken as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(PageSerializer(page).data, status=status.HTTP_201_CREATED)


class PageDetailView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(responses=PageSerializer)
    def get(self, request, path):
        return Response(PageSerializer(get_own_page(request, path)).data)

    @extend_schema(
        request=PageEditSerializer,
        responses={200: PageSerializer, 400: INVALID, 409: CONFLICT},
    )
    def put(self, request, path):
        page = get_own_page(request, path)
        serializer = PageEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            page = services.edit_page(page, **serializer.validated_data)
        except okf.OKFError as e:
            return Response({e.field: [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except services.StaleVersion as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(PageSerializer(page).data)


class PageVersionListView(generics.ListAPIView):
    """Historia, newest first, paginated."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PageVersionSerializer

    def get_queryset(self):
        # drf-spectacular calls this without a user while building the schema
        if getattr(self, "swagger_fake_view", False):
            return PageVersion.objects.none()
        return get_own_page(self.request, self.kwargs["path"]).versions.all()
```

- [ ] **Step 6: Implement `wiki/urls.py`**

```python
from django.urls import path, re_path

from wiki.views import PageDetailView, PageListCreateView, PageVersionListView

# Path without the leading '/': 'books/solaris.md'
PAGE_PATH = r"(?P<path>(?:books|characters|places|universes)/[a-z0-9-]+\.md)"

urlpatterns = [
    path("pages/", PageListCreateView.as_view(), name="wiki-pages"),
    re_path(rf"^pages/{PAGE_PATH}$", PageDetailView.as_view(), name="wiki-page"),
    re_path(
        rf"^pages/{PAGE_PATH}/versions/$",
        PageVersionListView.as_view(),
        name="wiki-page-versions",
    ),
]
```

- [ ] **Step 7: Mount it** in `config/urls.py`, after `path("api/u/", include("users.urls.public")),`:

```python
    path("api/u/", include("users.urls.public")),
    path("api/wiki/", include("wiki.urls")),
```

- [ ] **Step 8: Run the tests**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_pages_api.py -q`
Expected: `17 passed`.

- [ ] **Step 9: Lint**

Run: `uv run ruff check .` → `All checks passed!`

- [ ] **Step 10: Commit**

```bash
git add backend-django/wiki backend-django/config/urls.py
```
```bash
git commit -m "feat: add wiki pages API with versions [#108]"
```

---

### Task 4: Seed command and fixtures

**Files:**
- Create: `backend-django/wiki/fixtures/{books,characters,places,universes}/*.md` (copies)
- Create: `backend-django/wiki/management/__init__.py`, `wiki/management/commands/__init__.py` (empty), `wiki/management/commands/seed.py`
- Test: `backend-django/wiki/tests/test_seed.py`

- [ ] **Step 1: Copy the fixtures** (from the worktree root; two separate commands)

```bash
mkdir -p backend-django/wiki/fixtures
```
```bash
cp -r frontend/src/api/fixtures/books frontend/src/api/fixtures/characters frontend/src/api/fixtures/places frontend/src/api/fixtures/universes backend-django/wiki/fixtures/
```

Check: `find backend-django/wiki/fixtures -name '*.md' | wc -l` → `15`

- [ ] **Step 2: Write the failing tests** — `wiki/tests/test_seed.py`

```python
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from config.test_helpers import AuthTestHelper
from wiki.models import Page, PageVersion


def seed(email):
    out = StringIO()
    call_command("seed", email, stdout=out)
    return out.getvalue()


class SeedTest(AuthTestHelper, TestCase):
    @classmethod
    def setUpTestData(cls):
        AuthTestHelper.setUpTestData()

    def test_loads_every_fixture_with_one_created_version(self):
        self.assertIn("created 15, skipped 0", seed("user@test.com"))
        self.assertEqual(Page.objects.filter(owner=self.user).count(), 15)
        self.assertEqual(
            PageVersion.objects.filter(page__owner=self.user, kind="created").count(), 15
        )
        geralt = Page.objects.get(owner=self.user, path="/characters/geralt--krew-elfow.md")
        self.assertEqual((geralt.type, geralt.book), ("character", "/books/krew-elfow.md"))

    def test_second_run_skips_existing_pages(self):
        seed("user@test.com")
        self.assertIn("created 0, skipped 15", seed("user@test.com"))
        self.assertEqual(PageVersion.objects.filter(page__owner=self.user).count(), 15)

    def test_unknown_email_fails(self):
        with self.assertRaises(CommandError):
            seed("nobody@test.com")
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_seed.py -q`
Expected: `CommandError: Unknown command: 'seed'` in 3 tests (the third may pass by accident: that's fine).

- [ ] **Step 4: Implement `wiki/management/commands/seed.py`** (plus the two empty `__init__.py` files)

```python
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from users.models import User
from wiki import okf, services

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class Command(BaseCommand):
    help = "Load the Wiedźmin + Solaris demo Pages into a user's Wiki (existing Paths skipped)"

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, email, **options):
        try:
            owner = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            raise CommandError(f"No user with email {email}") from None
        created = skipped = 0
        for page_type, directory in okf.DIRS.items():
            for file in sorted((FIXTURES / directory).glob("*.md")):
                path = f"/{directory}/{file.name}"
                try:
                    services.insert_page(owner, path, page_type, file.read_text(encoding="utf-8"))
                except services.PathTaken:
                    skipped += 1
                except okf.OKFError as e:
                    raise CommandError(f"{path}: {e}") from e
                else:
                    created += 1
        self.stdout.write(f"created {created}, skipped {skipped}")
```

- [ ] **Step 5: Run the tests**

Run: `DJANGO_ENV=dev uv run --env-file ../infra/.env python -m pytest wiki/tests/test_seed.py -q`
Expected: `3 passed`. If `CommandError: /…md: Missing template headings…`, fix that fixture in `backend-django/wiki/fixtures/` (not in `frontend/`) and rerun.

- [ ] **Step 6: Lint**

Run: `uv run ruff check .` → `All checks passed!`

- [ ] **Step 7: Commit**

```bash
git add backend-django/wiki
```
```bash
git commit -m "feat: add wiki seed command with fixtures [#108]"
```

---

### Task 5: OpenAPI snapshot, docs, full verify

**Files:**
- Modify: `docs/api/openapi.yml` (generated), `docs/ARCHITECTURE.md` (data model section)

- [ ] **Step 1: Regenerate the snapshot** (from the worktree root)

Run: `make regenerate-openapi`
Expected: `OpenAPI snapshot updated: …/docs/api/openapi.yml`; `git diff --stat docs/api/openapi.yml` shows additions only under `/api/wiki/` paths and new `Page*` schemas.

- [ ] **Step 2: Note the current Version rule** in `docs/ARCHITECTURE.md`, right after the line starting `Pola z frontmattera potrzebne do zapytań`:

```markdown
Aktualna Wersja Strony to jej najnowszy `PageVersion` (bez osobnego wskaźnika). API zwraca jej id jako `version`, a Edycja odsyła je jako `base_version`; nieaktualne → 409.
```

- [ ] **Step 3: Install frontend deps** (needed by `make verify`; from the worktree root)

Run: `npm ci --prefix frontend`

- [ ] **Step 4: Full verify** (from the worktree root)

Run: `make verify`
Expected: ruff clean, `manage.py check` clean, pytest all passed (users + wiki), `test_openapi_schema` OK, frontend typecheck/lint/format/test pass.

- [ ] **Step 5: Commit**

```bash
git add docs/api/openapi.yml docs/ARCHITECTURE.md
```
```bash
git commit -m "docs: regenerate OpenAPI for wiki pages [#108]"
```

---

## Done when (from #108) → where it is checked

| # | Criterion | Test |
|---|---|---|
| 1 | Missing `type`, wrong `type`, removed heading → 400 with field message | `test_create_without_type_returns_400_on_type`, `test_create_with_unknown_type_returns_400_on_type`, `test_edit_changing_type_returns_400`, `test_edit_without_template_heading_returns_400`, `ValidateTest` |
| 2 | Each create/edit adds a Version; versions newest first | `test_create_book_returns_template_page_with_created_version`, `test_edit_adds_version_and_updates_title_but_not_path` |
| 3 | Outdated `base_version` → 409, nothing changes | `test_stale_base_version_returns_409_and_changes_nothing` |
| 4 | User A gets 404 for User B's Pages | `test_other_users_page_returns_404`, `test_list_filters_by_type_and_hides_content` |
| 5 | `seed` loads fixtures; `make verify` incl. OpenAPI test | `SeedTest`, Task 5 Step 4 |
