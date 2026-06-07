# M14 — Typed Character Relations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the free-text `CharacterRelation.label` with a controlled vocabulary of ~20 relation types in 7 colour-groups, colour the ego-graph by group, and render one node per character with coloured type pills.

**Architecture:** New `characters/relations.py` holds the `RelationType` enum + group mapping (single source of truth). The model swaps `label` → `relation_type` (+ unique `(from, to, type)`). The LLM prompt injects the allowed type list; `store_characters` validates and falls back to `OTHER`. The serializer exposes `type`/`type_display`/`group`; the Svelte `RelationGraph` groups relations per target character and renders coloured pills + a legend.

**Tech Stack:** Django 6 + DRF, PostgreSQL, drf-spectacular, SvelteKit 2 / Svelte 5 (runes), TypeScript.

**Branch:** `feat/m14-typed-relations` (already created, spec committed).

**Commands cheat-sheet:**
- Backend tests (all): from `backend-django/`, `DJANGO_ENV=dev uv run python manage.py test`
- Backend tests (one module): `DJANGO_ENV=dev uv run python manage.py test characters.tests.test_relations -v 2`
- Lint: from `backend-django/`, `uv run ruff check .`
- OpenAPI regen: from repo root, `make regenerate-openapi`
- Frontend check: from `svelte-frontend/`, `npm run check`

---

### Task 1: Relation taxonomy module

**Files:**
- Create: `backend-django/characters/relations.py`
- Test: `backend-django/characters/tests/test_relations.py`

- [ ] **Step 1: Write the failing test**

Create `backend-django/characters/tests/test_relations.py`:

```python
from django.test import SimpleTestCase

from characters.relations import RelationType, relation_group


class RelationGroupTests(SimpleTestCase):
    def test_known_types_map_to_groups(self):
        self.assertEqual(relation_group(RelationType.PARENT), "family")
        self.assertEqual(relation_group(RelationType.LOVER), "romance")
        self.assertEqual(relation_group(RelationType.FRIEND), "friendship")
        self.assertEqual(relation_group(RelationType.MENTOR), "mentorship")
        self.assertEqual(relation_group(RelationType.MASTER), "power")
        self.assertEqual(relation_group(RelationType.ENEMY), "conflict")
        self.assertEqual(relation_group(RelationType.OTHER), "other")

    def test_unknown_type_maps_to_other(self):
        self.assertEqual(relation_group("nonsense"), "other")

    def test_every_type_has_a_valid_group(self):
        groups = {"family", "romance", "friendship", "mentorship", "power", "conflict", "other"}
        for value in RelationType.values:
            self.assertIn(relation_group(value), groups)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_relations -v 2`
Expected: FAIL — `ModuleNotFoundError: No module named 'characters.relations'`

- [ ] **Step 3: Write the module**

Create `backend-django/characters/relations.py`:

```python
from django.db import models


class RelationType(models.TextChoices):
    PARENT = "parent", "Parent"
    CHILD = "child", "Child"
    SIBLING = "sibling", "Sibling"
    SPOUSE = "spouse", "Spouse"
    RELATIVE = "relative", "Relative"
    LOVER = "lover", "Lover"
    EX_PARTNER = "ex_partner", "Ex-partner"
    FRIEND = "friend", "Friend"
    ALLY = "ally", "Ally"
    MENTOR = "mentor", "Mentor"
    MENTEE = "mentee", "Mentee"
    MASTER = "master", "Master"
    SERVANT = "servant", "Servant"
    LEADER = "leader", "Leader"
    FOLLOWER = "follower", "Follower"
    ENEMY = "enemy", "Enemy"
    RIVAL = "rival", "Rival"
    COLLEAGUE = "colleague", "Colleague"
    ACQUAINTANCE = "acquaintance", "Acquaintance"
    OTHER = "other", "Other"


# Colour-group membership. Group is derived, never stored on the model.
_GROUP_MEMBERS = {
    "family": (
        RelationType.PARENT,
        RelationType.CHILD,
        RelationType.SIBLING,
        RelationType.SPOUSE,
        RelationType.RELATIVE,
    ),
    "romance": (RelationType.LOVER, RelationType.EX_PARTNER),
    "friendship": (RelationType.FRIEND, RelationType.ALLY),
    "mentorship": (RelationType.MENTOR, RelationType.MENTEE),
    "power": (
        RelationType.MASTER,
        RelationType.SERVANT,
        RelationType.LEADER,
        RelationType.FOLLOWER,
    ),
    "conflict": (RelationType.ENEMY, RelationType.RIVAL),
    "other": (RelationType.COLLEAGUE, RelationType.ACQUAINTANCE, RelationType.OTHER),
}

RELATION_GROUPS = {t: group for group, members in _GROUP_MEMBERS.items() for t in members}


def relation_group(relation_type: str) -> str:
    """Colour-group for a relation type; unknown values map to 'other'."""
    return RELATION_GROUPS.get(relation_type, "other")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_relations -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Lint + commit**

```bash
cd backend-django && uv run ruff check characters/relations.py characters/tests/test_relations.py
git add backend-django/characters/relations.py backend-django/characters/tests/test_relations.py
git commit -m "feat: add relation type taxonomy"
```

---

### Task 2: Model field + migration

**Files:**
- Modify: `backend-django/characters/models.py:53-66` (the `CharacterRelation` class)
- Create (generated): `backend-django/characters/migrations/0002_relation_type.py`
- Test: `backend-django/characters/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `backend-django/characters/tests/test_models.py`:

```python
from django.db import IntegrityError
from django.test import TestCase

from books.models import Book
from characters.models import Character, CharacterRelation
from characters.relations import RelationType


class CharacterRelationModelTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title="Dune")
        self.a = Character.objects.create(book=self.book, name="Paul", slug="paul", order=0)
        self.b = Character.objects.create(book=self.book, name="Jess", slug="jess", order=1)

    def test_group_property(self):
        rel = CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.PARENT,
        )
        self.assertEqual(rel.group, "family")

    def test_unique_per_type_blocks_duplicate(self):
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.SIBLING,
        )
        with self.assertRaises(IntegrityError):
            CharacterRelation.objects.create(
                book=self.book,
                from_character=self.a,
                to_character=self.b,
                relation_type=RelationType.SIBLING,
            )

    def test_same_pair_different_types_allowed(self):
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.SPOUSE,
        )
        CharacterRelation.objects.create(
            book=self.book,
            from_character=self.a,
            to_character=self.b,
            relation_type=RelationType.ENEMY,
        )
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_models -v 2`
Expected: FAIL — `TypeError`/`FieldError` referencing `relation_type` (field does not exist yet)

- [ ] **Step 3: Edit the model**

In `backend-django/characters/models.py`, add to the imports at the top (after the existing `from django.utils.text import slugify`):

```python
from .relations import RelationType, relation_group
```

Replace the entire `CharacterRelation` class (currently lines 53-66) with:

```python
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
    relation_type = models.CharField(
        max_length=20, choices=RelationType.choices, default=RelationType.OTHER
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_character", "to_character", "relation_type"],
                name="unique_relation_type_per_pair",
            ),
        ]

    @property
    def group(self) -> str:
        return relation_group(self.relation_type)

    def __str__(self):
        return f"{self.from_character.name} → {self.to_character.name} ({self.relation_type})"
```

> The `default=RelationType.OTHER` keeps `makemigrations` non-interactive (no one-off-default prompt when adding the column) and acts as a DB-level safety net. Application code always sets `relation_type` explicitly.

- [ ] **Step 4: Generate the migration**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py makemigrations characters`
Expected: creates `characters/migrations/0002_*.py` containing `RemoveField(label)`, `AddField(relation_type, default='other')`, and `AddConstraint(unique_relation_type_per_pair)` — NO interactive prompt.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_models -v 2`
Expected: PASS (3 tests). (The test runner builds a fresh schema from migrations.)

- [ ] **Step 6: Migrate the live dev DB**

Existing `CharacterRelation` rows are regenerable (delete-and-replace on every generation). Clear character data first so the new unique constraint cannot clash, then migrate:

```bash
cd backend-django && DATABASE_URL="postgres://postgres:CHANGE_ME@localhost:5432/booksdb" DJANGO_ENV=dev uv run python manage.py shell -c "from characters.models import Character; Character.objects.all().delete()"
DATABASE_URL="postgres://postgres:CHANGE_ME@localhost:5432/booksdb" DJANGO_ENV=dev uv run python manage.py migrate characters
```

Expected: `Applying characters.0002_... OK`. (If the dev stack is down or you only run tests, skip this step — the test DB is rebuilt from migrations anyway.)

- [ ] **Step 7: Lint + commit**

```bash
cd backend-django && uv run ruff check characters/models.py characters/tests/test_models.py
git add backend-django/characters/models.py backend-django/characters/migrations/0002_*.py backend-django/characters/tests/test_models.py
git commit -m "feat: typed relation_type field + migration"
```

---

### Task 3: LLM prompt uses the type list

**Files:**
- Modify: `backend-django/characters/ai.py:15-27` (PROMPT + `_build_prompt`)
- Test: `backend-django/characters/tests/test_ai.py:43-59` (update existing) + new prompt test

- [ ] **Step 1: Update the failing tests**

In `backend-django/characters/tests/test_ai.py`, replace the `test_parses_characters_and_relations` method (lines 43-59) with the version below, and add the new `test_prompt_lists_relation_types` method right after it:

```python
    def test_parses_characters_and_relations(self):
        body = _openrouter_response(
            {
                "characters": [
                    {"name": "Paul Atreides", "role": "Protagonist", "description": "Heir."},
                ],
                "relations": [
                    {"from": "Paul Atreides", "to": "Lady Jessica", "type": "parent"},
                ],
            }
        )

        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            data = generate_characters(FakeBook())

        self.assertEqual(data["characters"][0]["name"], "Paul Atreides")
        self.assertEqual(data["relations"][0]["type"], "parent")

    def test_prompt_lists_relation_types(self):
        from characters.ai import _build_prompt

        prompt = _build_prompt(FakeBook())
        self.assertIn("parent", prompt)
        self.assertIn("other", prompt)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_ai -v 2`
Expected: FAIL — `test_prompt_lists_relation_types` fails because the prompt does not yet contain the type list (`parent` not in prompt).

- [ ] **Step 3: Update the prompt**

In `backend-django/characters/ai.py`, add to the imports (after `from django.conf import settings`):

```python
from .relations import RelationType
```

Replace the `PROMPT` constant and `_build_prompt` (lines 15-27) with:

```python
_RELATION_TYPES = ", ".join(RelationType.values)

PROMPT = (
    'For the book "{title}" by {authors}, list the up to {limit} characters most '
    "important to the story. Return STRICT JSON only, no prose, matching exactly:\n"
    '{{"characters": [{{"name": str, "role": short str, "description": one paragraph}}], '
    '"relations": [{{"from": character name, "to": character name, "type": relation type}}]}}\n'
    "Use only character names that appear in the characters list for relations. "
    'Each relation "type" MUST be exactly one of: {types}. '
    'The type is the role of "to" relative to "from" '
    "(e.g. from=child, to=parent -> parent). If unsure which type fits, use other. "
    "If you do not know the book, return empty lists."
)


def _build_prompt(book) -> str:
    authors = ", ".join(book.authors.values_list("name", flat=True)) or "an unknown author"
    return PROMPT.format(
        title=book.title, authors=authors, limit=MAX_CHARACTERS, types=_RELATION_TYPES
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_ai -v 2`
Expected: PASS (6 tests)

- [ ] **Step 5: Lint + commit**

```bash
cd backend-django && uv run ruff check characters/ai.py characters/tests/test_ai.py
git add backend-django/characters/ai.py backend-django/characters/tests/test_ai.py
git commit -m "feat: prompt emits typed relations"
```

---

### Task 4: Validate + store relation types

**Files:**
- Modify: `backend-django/characters/services.py:35-47` (the relations loop)
- Test: `backend-django/characters/tests/test_services.py` (full rewrite — every relation now uses `type`)

- [ ] **Step 1: Update the failing tests**

Replace the entire contents of `backend-django/characters/tests/test_services.py` with:

```python
from django.test import TestCase

from books.models import Book
from characters.ai import MAX_CHARACTERS
from characters.models import Character, CharacterRelation
from characters.relations import RelationType
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
                {"from": "Paul Atreides", "to": "Lady Jessica", "type": "parent"},
            ],
        }
        store_characters(self.book, data)

        self.assertEqual(Character.objects.filter(book=self.book).count(), 2)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.from_character.name, "Paul Atreides")
        self.assertEqual(rel.to_character.name, "Lady Jessica")
        self.assertEqual(rel.relation_type, RelationType.PARENT)
        self.assertEqual(Character.objects.get(name="Paul Atreides").order, 0)

    def test_caps_at_12_characters(self):
        data = {
            "characters": [
                {"name": f"Char {i}", "role": "x", "description": "y"} for i in range(20)
            ],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), MAX_CHARACTERS)

    def test_skips_relations_with_unknown_endpoints(self):
        data = {
            "characters": [{"name": "Paul", "role": "x", "description": "y"}],
            "relations": [{"from": "Paul", "to": "Ghost", "type": "friend"}],
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

    def test_skips_non_dict_character_items(self):
        data = {
            "characters": [None, "Paul", {"name": "Real", "role": "x", "description": "y"}],
            "relations": [],
        }
        store_characters(self.book, data)
        self.assertEqual(Character.objects.filter(book=self.book).count(), 1)
        self.assertEqual(Character.objects.get(book=self.book).name, "Real")

    def test_skips_self_relation(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Paul", "type": "sibling"}],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 0)

    def test_dedupes_same_pair_and_type(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [
                {"from": "Paul", "to": "Jess", "type": "friend"},
                {"from": "Paul", "to": "Jess", "type": "friend"},
            ],
        }
        store_characters(self.book, data)
        self.assertEqual(CharacterRelation.objects.filter(book=self.book).count(), 1)

    def test_same_pair_different_types_kept(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Chani", "role": "x", "description": "y"},
            ],
            "relations": [
                {"from": "Paul", "to": "Chani", "type": "lover"},
                {"from": "Paul", "to": "Chani", "type": "ally"},
            ],
        }
        store_characters(self.book, data)
        types = set(
            CharacterRelation.objects.filter(book=self.book).values_list(
                "relation_type", flat=True
            )
        )
        self.assertEqual(types, {RelationType.LOVER, RelationType.ALLY})

    def test_unknown_type_falls_back_to_other(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Jess", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Jess", "type": "frenemy"}],
        }
        store_characters(self.book, data)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.relation_type, RelationType.OTHER)

    def test_type_matching_is_case_insensitive(self):
        data = {
            "characters": [
                {"name": "Paul", "role": "x", "description": "y"},
                {"name": "Leto", "role": "x", "description": "y"},
            ],
            "relations": [{"from": "Paul", "to": "Leto", "type": "PARENT"}],
        }
        store_characters(self.book, data)
        rel = CharacterRelation.objects.get(book=self.book)
        self.assertEqual(rel.relation_type, RelationType.PARENT)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_services -v 2`
Expected: FAIL — `store_characters` still reads `label`, so `relation_type` is the `OTHER` default everywhere; `test_creates_characters_and_relations`, `test_same_pair_different_types_kept`, `test_type_matching_is_case_insensitive` fail.

- [ ] **Step 3: Update the service**

In `backend-django/characters/services.py`, add to the imports (after `from .ai import MAX_CHARACTERS`):

```python
from .relations import RelationType
```

Replace the relations loop (lines 35-47, from `seen: set[tuple] = set()` to the end of the function) with:

```python
    valid_types = set(RelationType.values)
    seen: set[tuple] = set()
    for rel in data.get("relations", []):
        if not isinstance(rel, dict):
            continue
        source = by_name.get((rel.get("from") or "").strip())
        target = by_name.get((rel.get("to") or "").strip())
        raw_type = (rel.get("type") or "").strip().lower()
        relation_type = raw_type if raw_type in valid_types else RelationType.OTHER
        key = (id(source), id(target), relation_type)
        if source and target and source != target and key not in seen:
            seen.add(key)
            CharacterRelation.objects.create(
                book=book,
                from_character=source,
                to_character=target,
                relation_type=relation_type,
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_services -v 2`
Expected: PASS (10 tests)

- [ ] **Step 5: Lint + commit**

```bash
cd backend-django && uv run ruff check characters/services.py characters/tests/test_services.py
git add backend-django/characters/services.py backend-django/characters/tests/test_services.py
git commit -m "feat: validate + store typed relations"
```

---

### Task 5: Serializer exposes type/type_display/group

**Files:**
- Modify: `backend-django/characters/serializers.py:13-16` (the `CharacterRelationSerializer`)
- Test: `backend-django/characters/tests/test_api.py:51-62` (the `test_detail_returns_relations` method)

- [ ] **Step 1: Update the failing test**

In `backend-django/characters/tests/test_api.py`, replace the `test_detail_returns_relations` method (lines 51-62) with:

```python
    def test_detail_returns_relations(self):
        paul = Character.objects.create(book=self.book, name="Paul", slug="paul", order=0)
        jess = Character.objects.create(book=self.book, name="Jessica", slug="jessica", order=1)
        from characters.models import CharacterRelation
        from characters.relations import RelationType

        CharacterRelation.objects.create(
            book=self.book,
            from_character=paul,
            to_character=jess,
            relation_type=RelationType.PARENT,
        )
        res = self.client.get(f"/api/books/{self.book.slug}/characters/paul/")
        self.assertEqual(res.status_code, 200)
        rel = res.data["relations"][0]
        self.assertEqual(rel["to_slug"], "jessica")
        self.assertEqual(rel["type"], "parent")
        self.assertEqual(rel["type_display"], "Parent")
        self.assertEqual(rel["group"], "family")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_api -v 2`
Expected: FAIL — `KeyError: 'type'` (serializer still outputs `label`).

- [ ] **Step 3: Update the serializer**

In `backend-django/characters/serializers.py`, replace the `CharacterRelationSerializer` class (lines 13-16) with:

```python
class CharacterRelationSerializer(serializers.Serializer):
    to_slug = serializers.CharField(source="to_character.slug")
    to_name = serializers.CharField(source="to_character.name")
    type = serializers.CharField(source="relation_type")
    type_display = serializers.CharField(source="get_relation_type_display")
    group = serializers.CharField()
```

> `source="get_relation_type_display"` — DRF calls the model's auto-generated display method. `group` reads the model's `group` property.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test characters.tests.test_api -v 2`
Expected: PASS (5 tests)

- [ ] **Step 5: Run the whole backend suite**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test`
Expected: PASS (all tests; characters app green).

- [ ] **Step 6: Lint + commit**

```bash
cd backend-django && uv run ruff check characters/serializers.py characters/tests/test_api.py
git add backend-django/characters/serializers.py backend-django/characters/tests/test_api.py
git commit -m "feat: serialize relation type + group"
```

---

### Task 6: Regenerate OpenAPI snapshot

**Files:**
- Modify: `docs/api/openapi.yml` (regenerated)

- [ ] **Step 1: Confirm the contract test currently fails**

The serializer change altered the `CharacterRelation` schema, so the committed snapshot is stale.

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema -v 2`
Expected: FAIL — generated schema differs from `docs/api/openapi.yml` (relation fields changed).

- [ ] **Step 2: Regenerate the snapshot**

Run: `make regenerate-openapi`
Expected: `docs/api/openapi.yml` updated; the `CharacterRelation` component now lists `to_slug`, `to_name`, `type`, `type_display`, `group`.

- [ ] **Step 3: Verify the contract test passes**

Run: `cd backend-django && DJANGO_ENV=dev uv run python manage.py test config.tests.test_openapi_schema -v 2`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.yml
git commit -m "docs: regenerate OpenAPI for typed relations"
```

---

### Task 7: Frontend — type + colour-grouped graph

**Files:**
- Modify: `svelte-frontend/src/lib/types/character.ts:9-13` (the `CharacterRelation` interface)
- Modify: `svelte-frontend/src/lib/components/character/RelationGraph.svelte` (full rewrite)

- [ ] **Step 1: Update the type**

In `svelte-frontend/src/lib/types/character.ts`, replace the `CharacterRelation` interface (lines 9-13) with:

```ts
export interface CharacterRelation {
	to_slug: string;
	to_name: string;
	type: string;
	type_display: string;
	group: string;
}
```

- [ ] **Step 2: Rewrite the graph component**

Replace the entire contents of `svelte-frontend/src/lib/components/character/RelationGraph.svelte` with:

```svelte
<script lang="ts">
	import type { CharacterRelation } from '$lib/types/character';
	import { initials, monogramColor } from '$lib/utils/monogram';

	let {
		centerName,
		bookSlug,
		relations
	}: { centerName: string; bookSlug: string; relations: CharacterRelation[] } = $props();

	// Colour per relation group (matches the approved mockup).
	const GROUP_COLORS: Record<string, string> = {
		family: '#d97706',
		romance: '#db2777',
		friendship: '#16a34a',
		mentorship: '#2563eb',
		power: '#7c3aed',
		conflict: '#dc2626',
		other: '#6b7280'
	};
	const groupColor = (g: string) => GROUP_COLORS[g] ?? GROUP_COLORS.other;

	const W = 360;
	const H = 360;
	const CX = W / 2;
	const CY = H / 2;
	const R = 130;

	type Pill = { type: string; type_display: string; group: string };
	type Related = { to_slug: string; to_name: string; pills: Pill[] };

	// One node per related character; collect every relation type pointing to it.
	const characters = $derived.by(() => {
		const map = new Map<string, Related>();
		for (const rel of relations) {
			let entry = map.get(rel.to_slug);
			if (!entry) {
				entry = { to_slug: rel.to_slug, to_name: rel.to_name, pills: [] };
				map.set(rel.to_slug, entry);
			}
			entry.pills.push({ type: rel.type, type_display: rel.type_display, group: rel.group });
		}
		return [...map.values()];
	});

	const nodes = $derived(
		characters.map((c, i) => {
			const angle = (2 * Math.PI * i) / Math.max(characters.length, 1) - Math.PI / 2;
			return { c, x: CX + R * Math.cos(angle), y: CY + R * Math.sin(angle) };
		})
	);

	// Groups present in this graph, for the legend.
	const legendGroups = $derived([...new Set(relations.map((r) => r.group))]);
</script>

{#if relations.length === 0}
	<p class="text-sm text-muted">No relations recorded.</p>
{:else}
	<svg viewBox="0 0 {W} {H}" class="w-full max-w-md rounded-xl border border-rule bg-surface">
		{#each nodes as node (node.c.to_slug)}
			<line x1={CX} y1={CY} x2={node.x} y2={node.y} stroke="#8884" stroke-width="2" />
		{/each}

		{#each nodes as node (node.c.to_slug)}
			{#each node.c.pills as pill, j (`${node.c.to_slug}::${pill.type}`)}
				{@const mx = (CX + node.x) / 2}
				{@const my = (CY + node.y) / 2 + (j - (node.c.pills.length - 1) / 2) * 20}
				{@const w = pill.type_display.length * 6.6 + 16}
				<rect x={mx - w / 2} y={my - 9} width={w} height="18" rx="9" fill={groupColor(pill.group)} />
				<text x={mx} y={my + 4} fill="#fff" font-size="11" text-anchor="middle">
					{pill.type_display}
				</text>
			{/each}
		{/each}

		{#each nodes as node (node.c.to_slug)}
			<a href="/books/{bookSlug}/characters/{node.c.to_slug}" aria-label={node.c.to_name}>
				<circle cx={node.x} cy={node.y} r="26" fill={monogramColor(node.c.to_name)} />
				<text x={node.x} y={node.y + 4} fill="#fff" font-size="12" text-anchor="middle">
					{initials(node.c.to_name)}
				</text>
			</a>
		{/each}

		<circle cx={CX} cy={CY} r="32" fill={monogramColor(centerName)} stroke="#fff" stroke-width="3" />
		<text x={CX} y={CY + 5} fill="#fff" font-size="14" font-weight="bold" text-anchor="middle">
			{initials(centerName)}
		</text>
	</svg>

	<div class="mt-3 flex flex-wrap gap-2">
		{#each legendGroups as g (g)}
			<span class="rounded-full px-3 py-1 text-xs capitalize text-white" style="background:{groupColor(g)}">
				{g}
			</span>
		{/each}
	</div>
{/if}
```

- [ ] **Step 3: Run the frontend check**

Run: `cd svelte-frontend && npm run check`
Expected: PASS — no TypeScript/svelte-check errors (the old `label` reference is gone).

- [ ] **Step 4: Run lint**

Run: `cd svelte-frontend && npm run lint`
Expected: PASS (Prettier + ESLint clean). If Prettier reformats, re-run is clean.

- [ ] **Step 5: Commit**

```bash
git add svelte-frontend/src/lib/types/character.ts svelte-frontend/src/lib/components/character/RelationGraph.svelte
git commit -m "feat: colour-grouped relation graph + legend"
```

---

## Done criteria

- `DJANGO_ENV=dev uv run python manage.py test` — all green, including new `test_relations`, `test_models`, updated `test_services`/`test_ai`/`test_api`, and `config.tests.test_openapi_schema`.
- `uv run ruff check .` — clean.
- `npm run check` + `npm run lint` — clean.
- Ego-graph renders one node per character with colour-coded type pills + legend; a pair with two relations shows two pills on one node.
