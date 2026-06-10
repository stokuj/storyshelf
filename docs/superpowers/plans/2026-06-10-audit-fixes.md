# Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Naprawić 24 potwierdzone findings z holistycznego audytu (spec: `docs/superpowers/specs/2026-06-10-audit-fixes-design.md`).

**Architecture:** Zmiany punktowe w istniejących plikach — bez nowych modułów. Kolejność: CI → backend (+ regen OpenAPI raz) → frontend (typy → API → UI) → infra/tooling → testy → E2E seed → docs na końcu.

**Tech Stack:** Django 6 + DRF (uv, pytest), SvelteKit 2 + Svelte 5 (runes), Docker Compose, Caddy, GitHub Actions, Playwright.

**Gałąź:** `chore/holistic-audit` (kontynuacja). Commity konwencjonalne, tytuł ≤50 znaków, bez Co-Authored-By.

**Komendy weryfikacyjne** (z `backend-django/`, dev-stack musi działać — `make dev-up`):

```bash
# backend testy (z hosta):
DJANGO_ENV=dev DATABASE_URL=postgres://postgres:CHANGE_ME@localhost:5432/booksdb uv run python -m pytest -q
# lint:
uv run ruff check .
# frontend (z svelte-frontend/):
npm run check && npm run lint
```

(Hasło `CHANGE_ME` = wartość `POSTGRES_PASSWORD` z `infra/.env`. Po Tasku 13 wystarczy `make verify`.)

---

### Task 1: CI — gating build-and-push + pytest + cleanup (B1, część N6)

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Dodaj `needs:` do build-and-push**

W `.github/workflows/ci.yml` linia 71–72, zmień:

```yaml
  build-and-push:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

na:

```yaml
  build-and-push:
    needs: [lint, test, frontend]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
```

- [ ] **Step 2: Ujednolić runner testów na pytest**

Linia 47–49, zmień:

```yaml
      - name: Run Django tests
        working-directory: backend-django
        run: uv run python manage.py test --noinput
```

na:

```yaml
      - name: Run Django tests
        working-directory: backend-django
        run: uv run python -m pytest
```

(`DJANGO_ENV` i `DATABASE_URL` są już w `env:` joba `test` — linie 37–41. Krok „Verify OpenAPI snapshot" zostaje na `manage.py test` jak w Makefile.)

- [ ] **Step 3: Usuń martwy komentarz**

Usuń linię 89: `# SvelteKit build step added in phase/2.6-svelte-setup` (i pustą linię 90 jeśli zostaje wisząca).

- [ ] **Step 4: Walidacja YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo OK`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: gate image push on green jobs"
```

---

### Task 2: BookAdmin — pola liczone readonly (I2)

**Files:**
- Modify: `backend-django/books/admin.py`

- [ ] **Step 1: Dodaj readonly_fields**

W `books/admin.py` po linii 15 (`inlines = [BookAuthorInline]`) dodaj:

```python
    readonly_fields = ("avg_rating", "ratings_count")
```

(`fields` zostaje bez zmian — pola będą widoczne, ale nieedytowalne.)

- [ ] **Step 2: Sprawdź konfigurację admina**

Run (z `backend-django/`): `DJANGO_ENV=dev uv run python manage.py check`
Expected: `System check identified no issues`

- [ ] **Step 3: Commit**

```bash
git add books/admin.py
git commit -m "fix: readonly avg_rating in BookAdmin"
```

---

### Task 3: Usunięcie martwego endpointu GET /api/auth/me/ (I9)

**Files:**
- Modify: `backend-django/users/urls/auth.py`
- Modify: `backend-django/users/views.py:127-147` (klasa `AuthMeView`)
- Modify: `backend-django/users/tests/test_auth.py:154-…` (klasa `AuthMeTest`)
- NIE ruszaj: `users/tests/test_cookie_auth.py` — używa `/api/auth/me/` tylko jako stringa ścieżki dla `APIRequestFactory` (nie rezolwuje URL-i), działa dalej.

- [ ] **Step 1: Usuń trasę**

`users/urls/auth.py` — usuń linię `path("me/", AuthMeView.as_view()),` i `AuthMeView` z importu:

```python
from django.urls import path

from users.views import LoginView, LogoutView, RegisterView, TokenRefreshCookieView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("refresh/", TokenRefreshCookieView.as_view()),
    path("logout/", LogoutView.as_view()),
]
```

- [ ] **Step 2: Usuń widok**

`users/views.py` — usuń całą klasę `AuthMeView` (linie 127–147, wraz z docstringiem).

- [ ] **Step 3: Usuń testy widoku**

`users/tests/test_auth.py` — usuń całą klasę `AuthMeTest` (od linii 154 do końca jej ostatniego testu `test_get_unauthenticated_returns_200_with_false`).

- [ ] **Step 4: Testy users zielone**

Run: `DJANGO_ENV=dev DATABASE_URL=postgres://postgres:CHANGE_ME@localhost:5432/booksdb uv run python -m pytest users/ -q`
Expected: PASS (mniej testów o 2). Kontrakt OpenAPI będzie czerwony do Tasku 6 — to oczekiwane.

- [ ] **Step 5: Commit**

```bash
git add users/urls/auth.py users/views.py users/tests/test_auth.py
git commit -m "refactor: remove dead auth/me endpoint"
```

---

### Task 4: Backend — 400 przy braku book_slug (część N4, TDD)

**Files:**
- Modify: `backend-django/ratings/views.py:26-30`, `backend-django/reviews/views.py:58-62`
- Test: `backend-django/ratings/tests/test_api.py`, `backend-django/reviews/tests/test_api.py`

- [ ] **Step 1: Failing testy**

Do `ratings/tests/test_api.py` (w klasie `RatingAPITest`, obok `test_put_unknown_book_returns_404`):

```python
    def test_put_without_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put(URL, {"rating": 4}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book_slug", resp.data)
```

Do `reviews/tests/test_api.py` — klasa `ReviewAPITest` (ma `cls.user` i stałą `URL = "/api/reviews/"`), obok testów upsert:

```python
    def test_put_without_book_slug_returns_400(self):
        self.client.force_authenticate(self.user)
        resp = self.client.put("/api/reviews/", {"body": "x"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book_slug", resp.data)
```

- [ ] **Step 2: Potwierdź FAIL**

Run: `DJANGO_ENV=dev DATABASE_URL=... uv run python -m pytest ratings/ reviews/ -q -k book_slug`
Expected: 2 failed (dziś zwracają 404).

- [ ] **Step 3: Implementacja**

W OBU plikach (`ratings/views.py` metoda `update`, `reviews/views.py` metoda `update`) przed `try: book = Book.objects.get(...)` wstaw:

```python
        book_slug = request.data.get("book_slug")
        if not book_slug:
            return Response(
                {"book_slug": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
```

(usuń zduplikowaną linię `book_slug = request.data.get("book_slug")` która była niżej).

- [ ] **Step 4: Testy zielone**

Run: `... uv run python -m pytest ratings/ reviews/ -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add ratings/ reviews/
git commit -m "fix: 400 on missing book_slug in upserts"
```

---

### Task 5: Backend — serializacja dispatchu generacji (część N4, TDD)

**Files:**
- Modify: `backend-django/characters/views.py`
- Test: `backend-django/characters/tests/test_api.py`

- [ ] **Step 1: Nowe testy (re-dispatch DONE/FAILED, idempotencja PENDING) — z `captureOnCommitCallbacks`**

Do `characters/tests/test_api.py` w klasie `CharacterApiTests` dodaj:

```python
    def test_generate_redispatches_after_done(self):
        self.client.force_authenticate(self.user)
        CharacterAnalysis.objects.create(book=self.book, status=CharacterAnalysis.Status.DONE)
        with patch("characters.views.generate_characters_task.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "pending")
        delay.assert_called_once_with(self.book.id)

    def test_generate_redispatches_after_failed(self):
        self.client.force_authenticate(self.user)
        CharacterAnalysis.objects.create(
            book=self.book, status=CharacterAnalysis.Status.FAILED, error_message="boom"
        )
        with patch("characters.views.generate_characters_task.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        delay.assert_called_once_with(self.book.id)
        analysis = CharacterAnalysis.objects.get(book=self.book)
        self.assertEqual(analysis.error_message, "")

    def test_generate_is_idempotent_while_pending(self):
        self.client.force_authenticate(self.user)
        CharacterAnalysis.objects.create(book=self.book, status=CharacterAnalysis.Status.PENDING)
        with patch("characters.views.generate_characters_task.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                res = self.client.post(self._generate_url())
        self.assertEqual(res.status_code, 202)
        self.assertEqual(res.data["status"], "pending")
        delay.assert_not_called()
```

- [ ] **Step 2: Uruchom — DONE/FAILED przejdą już teraz (logika istnieje), upewnij się że PENDING też**

Run: `... uv run python -m pytest characters/tests/test_api.py -q`
Expected: PASS (te testy dokumentują istniejące zachowanie; race fix w Step 3 nie może ich zepsuć).

- [ ] **Step 3: Race fix — atomic + select_for_update + on_commit**

`characters/views.py` — dodaj import i przepisz `post`:

```python
from django.db import transaction
```

```python
    @extend_schema(request=None, responses={202: _status_response})
    def post(self, request, slug):
        book = get_object_or_404(Book, slug=slug)
        # Lock serialises concurrent generate requests for one book; on_commit
        # ensures the worker never sees an uncommitted analysis row.
        with transaction.atomic():
            analysis, created = CharacterAnalysis.objects.select_for_update().get_or_create(
                book=book
            )
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
                transaction.on_commit(lambda: generate_characters_task.delay(book.id))
        return Response({"status": analysis.status}, status=status.HTTP_202_ACCEPTED)
```

- [ ] **Step 4: Zaktualizuj 2 istniejące testy o `captureOnCommitCallbacks`**

W `test_generate_enqueues_and_returns_pending` i `test_generate_is_idempotent_while_running` opakuj `self.client.post(...)`:

```python
        with patch("characters.views.generate_characters_task.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                res = self.client.post(self._generate_url())
```

- [ ] **Step 5: Testy zielone**

Run: `... uv run python -m pytest characters/ -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add characters/
git commit -m "fix: serialize generate dispatch per book"
```

---

### Task 6: Backend — pozostałe nity N4 + N5 (nullability) + regen OpenAPI

**Files:**
- Modify: `backend-django/feed/serializers.py:13`
- Modify: `backend-django/users/models.py:70-72` + nowa migracja
- Modify: `backend-django/reviews/views.py:108` (komentarz)
- Modify: `backend-django/users/serializers.py:15,162` (min_length) i 4× `get_avatar_url`
- Modify: `backend-django/books/serializers.py:27`
- Regen: `docs/api/openapi.yml`

- [ ] **Step 1: FeedBookSerializer — allow_blank**

`feed/serializers.py:13`: `cover_url = serializers.CharField(allow_null=True)` → `cover_url = serializers.CharField(allow_blank=True)` (model ma `default=""`, nigdy null).

- [ ] **Step 2: Usuń redundantny index**

`users/models.py` — usuń cały blok `indexes = [...]` (linie 70–72; FK `following` ma automatyczny index Django).

- [ ] **Step 3: Migracja**

Run: `DJANGO_ENV=dev uv run python manage.py makemigrations users -n remove_following_index`
Expected: migracja z `RemoveIndex`. Następnie zaaplikuj na dev-DB:
`DJANGO_ENV=dev DATABASE_URL=postgres://postgres:CHANGE_ME@localhost:5432/booksdb uv run python manage.py migrate`

- [ ] **Step 4: Komentarz przy sortowaniu recenzji**

`reviews/views.py` w `UserReviewListView.get_queryset`, nad `order_by("-updated_at")`:

```python
        # Intentional: the public profile surfaces recently *edited* reviews,
        # while the global list (ReviewViewSet) orders by creation date.
```

- [ ] **Step 5: min_length hasła 6 → 8**

`users/serializers.py:15` i `:162` — w `RegisterSerializer.password` i `PasswordChangeSerializer.new_password` zmień `min_length=6` na `min_length=8` (front już wymaga 8 — `signup/+page.server.ts:17`).

- [ ] **Step 6: Nullability avatar_url (4×) i serie**

`users/serializers.py` — nad KAŻDĄ z 4 metod `get_avatar_url` (linie ~97, ~125, ~149, ~245) dodaj dekorator (`extend_schema_field` już jest w importach):

```python
    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_avatar_url(self, obj):
```

`books/serializers.py:27`: `serie = SerieSerializer(read_only=True)` → `serie = SerieSerializer(read_only=True, allow_null=True)`.

- [ ] **Step 7: Regeneruj snapshot OpenAPI**

Run (z roota): `make regenerate-openapi`
Expected: `docs/api/openapi.yml` zmienione — zniknie `/api/auth/me/`, `avatar_url`/`serie` dostaną `nullable: true`, `minLength: 8`.

- [ ] **Step 8: Pełny backend zielony**

Run: `DJANGO_ENV=dev DATABASE_URL=... uv run python -m pytest -q && uv run ruff check .`
Run: `DJANGO_ENV=dev DATABASE_URL=... uv run python manage.py test config.tests.test_openapi_schema --noinput`
Expected: wszystko PASS (388+3 nowe −2 usunięte ≈ 389).

- [ ] **Step 9: Commit**

```bash
git add feed/ users/ reviews/ books/ ../docs/api/openapi.yml
git commit -m "fix: backend nits + nullable openapi fields"
```

---

### Task 7: Frontend — rozdzielenie typów Book + PublicShelfEntry (I10)

**Files:**
- Modify: `svelte-frontend/src/lib/types/book.ts`
- Modify: `svelte-frontend/src/lib/api/books.ts:43,56`
- Modify: `svelte-frontend/src/lib/types/shelf.ts`, `src/lib/api/shelf.ts:9-11`
- Modify konsumenci: `src/lib/components/book/BookHeader.svelte:6`, `BookMeta.svelte:5`, `src/lib/components/discover/BookGridDiscover.svelte:7`, `src/routes/discover/+page.svelte` (import + `$state<Book[]>`)

- [ ] **Step 1: Nowe typy w book.ts**

Zastąp CAŁĄ zawartość `src/lib/types/book.ts` (usuwamy też martwy typ `Author` — zero użyć):

```ts
export type BookId = number;

export interface SerieInfo {
	id: number;
	name: string;
	description: string;
	status: string;
	created_at: string;
}

/** Shape returned by GET /api/books/ (BookListSerializer). */
export interface BookListItem {
	id: number;
	slug: string;
	title: string;
	authors: string[];
	cover_url: string | null;
	year: number | null;
	genres: string[];
	avg_rating: number;
}

/** Shape returned by GET /api/books/{slug}/ (BookDetailSerializer — no id). */
export interface BookDetail {
	slug: string;
	title: string;
	authors: string[];
	cover_url: string | null;
	year: number | null;
	isbn: string | null;
	genres: string[];
	tags: string[];
	description: string | null;
	page_count: number | null;
	avg_rating: number;
	ratings_count: number;
	position_in_series: number | null;
	serie: SerieInfo | null;
}
```

- [ ] **Step 2: api/books.ts — typy zwrotek**

```ts
import type { BookDetail, BookListItem } from '$lib/types';
```

`listBooks` → `apiFetch<PaginatedResponse<BookListItem>>`, `getBook` → `apiFetch<BookDetail>`.

- [ ] **Step 3: Konsumenci**

- `BookHeader.svelte` i `BookMeta.svelte`: `import type { BookDetail } from '$lib/types';` + prop `book: BookDetail;`
- `BookGridDiscover.svelte`: `import type { BookListItem } from '$lib/types/book';` + `books: BookListItem[];`
- `discover/+page.svelte`: import `BookListItem` zamiast `Book`, `let books = $state<BookListItem[]>(initialBooks);`
- Przejrzyj wynik `grep -rn "types/book'" src/` i `grep -rn "{ Book }" src/` — nie może zostać żaden import `Book`.

- [ ] **Step 4: PublicShelfEntry**

`src/lib/types/shelf.ts` — po interfejsie `ShelfEntry` dodaj:

```ts
/** GET /api/u/{handle}/shelf/ (PublicShelfEntrySerializer — no id). */
export type PublicShelfEntry = Omit<ShelfEntry, 'id'>;
```

`src/lib/api/shelf.ts` — `fetchPublicShelf` zwraca `apiFetch<PublicShelfEntry[]>` (dodaj `PublicShelfEntry` do importu typów). Sprawdź konsumenta: `src/routes/u/[handle]/` — jeśli typuje wynik jako `ShelfEntry[]`, zmień na `PublicShelfEntry[]` (kluczem listy jest `entry.book.slug`, nie `id` — bez zmian w markupie).

- [ ] **Step 5: Check**

Run (z `svelte-frontend/`): `npm run check`
Expected: 0 errors. Jeśli check wskaże użycie pola spoza `BookListItem` w gridzie — to realny bug typów, dopasuj pole do serializera (nie odwrotnie).

- [ ] **Step 6: Commit**

```bash
git add src/lib/types/ src/lib/api/ src/lib/components/ src/routes/
git commit -m "refactor: split Book types list/detail"
```

---

### Task 8: Frontend — books.ts isServerSide jako parametr (I11)

**Files:**
- Modify: `svelte-frontend/src/lib/api/books.ts`
- Modify: `src/routes/discover/+page.server.ts:10`, `src/routes/books/[slug]/+page.server.ts:15`

- [ ] **Step 1: Sygnatury**

`books.ts` — wzorzec jak w `shelf.ts`:

```ts
export async function listBooks(
	fetchFn: typeof fetch,
	params: ListBooksParams = {},
	isServerSide = false
) {
	// ... bez zmian ...
	return apiFetch<PaginatedResponse<BookListItem>>(
		fetchFn,
		`/books/${qs ? '?' + qs : ''}`,
		undefined,
		isServerSide
	);
}

export async function fetchGenres(fetchFn: typeof fetch, isServerSide = false) {
	return apiFetch<PaginatedResponse<Genre>>(fetchFn, '/genres/?per_page=100', undefined, isServerSide);
}

export async function getBook(fetchFn: typeof fetch, idOrSlug: string, isServerSide = false) {
	return apiFetch<BookDetail>(fetchFn, `/books/${idOrSlug}/`, undefined, isServerSide);
}
```

- [ ] **Step 2: Load functions przekazują `true`**

- `discover/+page.server.ts:10`: `listBooks(fetch, {...})` → `listBooks(fetch, {...}, true)`
- `books/[slug]/+page.server.ts:15`: `getBook(fetch, params.slug)` → `getBook(fetch, params.slug, true)`

Wywołania client-side w `discover/+page.svelte` (`loadBooks`, `loadMore`, `fetchGenres`) zostają bez trzeciego argumentu → idą na same-origin `/api`.

- [ ] **Step 3: Check + smoke**

Run: `npm run check`
Expected: 0 errors. Smoke (dev stack): `/discover` → load-more działa (request w devtools na `/api/books/...`).

- [ ] **Step 4: Commit**

```bash
git add src/lib/api/books.ts src/routes/
git commit -m "fix: isServerSide param in books api"
```

---

### Task 9: Frontend — N3 drobiazgi

**Files:**
- Modify: `svelte-frontend/package.json` (uninstall), `src/routes/discover/+page.svelte:73-78`, `src/lib/components/EmptyState.svelte:3-5`, `src/lib/components/discover/FilterBar.svelte`, 8 plików `$app/stores`

- [ ] **Step 1: Usuń martwe zależności**

Run: `npm uninstall @xyflow/svelte sveltekit-superforms`
Expected: `package.json` i `package-lock.json` bez obu wpisów.

- [ ] **Step 2: fetchGenres z obsługą błędu**

`discover/+page.svelte` — `$effect` (linie ~73–78):

```ts
	$effect(() => {
		if (genres.length === 0) {
			fetchGenres(fetch).then(({ data: result, error: apiErr }) => {
				if (result) genres = result.data;
				else if (apiErr) toast.error('Failed to load genres', { description: apiErr.detail });
			});
		}
	});
```

- [ ] **Step 3: ComponentType → Component**

`EmptyState.svelte`:

```ts
	import type { Component } from 'svelte';
	interface Props {
		icon: Component;
```

- [ ] **Step 4: Migracja $app/stores → $app/state (8 plików)**

Pliki: `src/lib/components/shell/AppShell.svelte`, `src/routes/+error.svelte`, `src/routes/settings/+layout.svelte`, `src/routes/settings/+page.svelte`, `src/routes/u/[handle]/+error.svelte`, `src/routes/books/[slug]/+error.svelte`, `src/routes/discover/+page.svelte`, `src/routes/shelf/+page.svelte`.

Wzorzec w każdym: `import { page } from '$app/stores';` → `import { page } from '$app/state';` oraz każde użycie `$page.` → `page.` (np. `$page.url.pathname` → `page.url.pathname`, `$page.data.user` → `page.data.user`, `new URL($page.url)` → `new URL(page.url)`, `$page.status` → `page.status`, `$page.error` → `page.error`).

UWAGA dla `settings/+page.svelte`: `let user = $derived($page.data.user ...)` → `let user = $derived(page.data.user as UserMe | null | undefined);` — `page` z `$app/state` jest reaktywne bez `$`.

- [ ] **Step 5: FilterBar — outside click przez refy**

`FilterBar.svelte` — dodaj refy i zamień `svelte:window` handler (wzorzec z `dropdown-menu.svelte`):

```ts
	let genreEl: HTMLElement | undefined = $state();
	let sortEl: HTMLElement | undefined = $state();
```

Na obu kontenerach dropdownów (`<div class="relative">` przy Genre i Sort) dodaj odpowiednio `bind:this={genreEl}` / `bind:this={sortEl}`. Handler na dole pliku:

```svelte
<svelte:window
	onclick={(e: MouseEvent) => {
		const target = e.target as Node;
		if (genreEl && !genreEl.contains(target) && sortEl && !sortEl.contains(target)) {
			genreOpen = false;
			sortOpen = false;
		}
	}}
/>
```

- [ ] **Step 6: Check + lint + build**

Run: `npm run check && npm run lint && npm run build`
Expected: 0 errors, build OK.

- [ ] **Step 7: Commit**

```bash
git add package.json package-lock.json src/
git commit -m "chore: frontend cleanups (deps, runes, refs)"
```

---

### Task 10: Frontend — /users loadError + phantom controls + feedback settings (I6, I7, I8)

**Files:**
- Modify: `src/routes/users/+page.svelte`
- Modify: `src/routes/settings/profile/+page.svelte`
- Modify: `src/routes/settings/+page.svelte`

- [ ] **Step 1: /users — toast na loadError**

`users/+page.svelte` — dodaj import `import { toast } from 'svelte-sonner';`, do destrukturyzacji `data` dodaj `loadError`, a po niej (wzorzec z `discover/+page.svelte:52-56`):

```ts
	const { initialUsers, initialTotal, initialSearch, initialOrdering, loadError } = data;

	if (loadError) {
		toast.error('Failed to load people', { description: loadError.detail });
	}
```

- [ ] **Step 2: settings/profile — usuń 3 phantom switche**

`settings/profile/+page.svelte` — usuń trzy bloki `<div class="flex items-center justify-between">…</div>` dla „Show real name", „Activity feed", „Search engine indexing" (linie ~26–46). Zostaje tylko switch `profile_public` + przycisk Save.

- [ ] **Step 3: settings — usuń statyczny pasek siły hasła**

`settings/+page.svelte` — usuń blok (linie ~100–106):

```svelte
			<!-- Simple password strength heuristic -->
			<div>
				<div class="w-full bg-rule rounded-full h-1.5">
					<div class="bg-accent rounded-full h-1.5" style="width: 25%"></div>
				</div>
				<p class="text-xs text-muted mt-1">Password strength: Weak</p>
			</div>
```

- [ ] **Step 4: Feedback formularzy — settings/+page.svelte**

Zmień `let {} = $props();` (i usuń `eslint-disable` nad nią) na:

```ts
	import { toast } from 'svelte-sonner';
	// ...
	let { form } = $props();

	$effect(() => {
		if (form?.error) toast.error(form.error as string);
		else if (form?.success) toast.success('Saved');
	});
```

- [ ] **Step 5: Feedback — settings/profile/+page.svelte**

```ts
	import { toast } from 'svelte-sonner';
	// ...
	let { data, form } = $props();

	$effect(() => {
		if (form?.error) toast.error(form.error as string);
		else if (form?.success) toast.success('Saved');
	});
```

- [ ] **Step 6: Check + smoke**

Run: `npm run check && npm run lint`
Expected: 0 errors. Smoke (dev): zła zmiana hasła (błędne current) → czerwony toast; zapis display name → „Saved".

- [ ] **Step 7: Commit**

```bash
git add src/routes/users/ src/routes/settings/
git commit -m "fix: settings feedback + drop phantom UI"
```

---

### Task 11: Frontend — chip filtra autora na /discover (I12)

**Files:**
- Modify: `src/routes/discover/+page.svelte`

- [ ] **Step 1: Funkcja czyszcząca + markup**

W skrypcie (obok `handleSearch`):

```ts
	function clearAuthor() {
		currentAuthor = '';
		loadBooks();
	}
```

W markupie bezpośrednio POD `<FilterBar …/>`:

```svelte
{#if currentAuthor}
	<div class="mb-4 -mt-4">
		<span
			class="inline-flex items-center gap-1.5 rounded-full border border-rule bg-surface px-3 py-1 text-sm text-ink"
		>
			Author: {currentAuthor}
			<button
				type="button"
				aria-label="Clear author filter"
				class="text-muted hover:text-ink"
				onclick={clearAuthor}
			>
				×
			</button>
		</span>
	</div>
{/if}
```

- [ ] **Step 2: Check + smoke**

Run: `npm run check`
Expected: 0 errors. Smoke: wejdź na `/discover?author=J.R.R.%20Tolkien` → chip widoczny, × czyści filtr i przeładowuje listę, URL traci `?author=`.

- [ ] **Step 3: Commit**

```bash
git add src/routes/discover/+page.svelte
git commit -m "feat: author filter chip on discover"
```

---

### Task 12: Frontend — paczka a11y (N2)

**Files:**
- Modify: `src/lib/components/ui/dropdown-menu/dropdown-menu-content.svelte`
- Modify: `src/lib/components/ui/dropdown-menu/dropdown-menu-trigger.svelte`
- Modify: `src/routes/settings/data/+page.svelte`
- Modify: `src/routes/shelf/+page.svelte`
- Modify: `src/lib/components/character/RelationGraph.svelte`

- [ ] **Step 1: Dropdown content — role="menu"**

`dropdown-menu-content.svelte` — do wewnętrznego `<div>` (ten z `cn(...)`) dodaj `role="menu"`.

- [ ] **Step 2: Trigger — aria**

`dropdown-menu-trigger.svelte` — context ma getter `open` (patrz `dropdown-menu.svelte`); rozszerz typ i dodaj atrybuty:

```ts
	const menu = getContext('dropdown-menu') as { open: boolean; toggle: () => void };
```

```svelte
<div
	class={cn('inline-flex items-center justify-center', className)}
	role="button"
	tabindex="0"
	aria-haspopup="menu"
	aria-expanded={menu.open}
	onclick={() => menu.toggle()}
	onkeydown={handleKeydown}
	{...restProps}
>
```

- [ ] **Step 3: Dialog delete — labelledby + Escape**

`settings/data/+page.svelte`:
- `<h2 class="…text-danger mb-2">` dostaje `id="delete-dialog-title"`.
- Outer dialog div: dodaj `aria-labelledby="delete-dialog-title"`.
- W bloku `{#if showDeleteDialog}` dodaj na początku:

```svelte
			<svelte:window onkeydown={(e) => { if (e.key === 'Escape') showDeleteDialog = false; }} />
```

- [ ] **Step 4: Tablisty /shelf — aria-controls + tabpanel**

`shelf/+page.svelte`:
- Zewnętrzny tablist: tab „Reading status" dostaje `aria-controls="panel-status"`, tab „My shelves" `aria-controls="panel-shelves"`.
- Wewnętrzny tablist (per status): każdy `<button role="tab">` w `{#each tabs}` dostaje `aria-controls="panel-status"`.
- Kontener treści dla widoku status (`{#if viewTab === 'status'}` — div z listą/empty state, zaraz po wewnętrznym tabliście) owiń/oznacz: `<div id="panel-status" role="tabpanel">…</div>`; analogicznie blok `{:else}` (My shelves) → `<div id="panel-shelves" role="tabpanel">…</div>`.

- [ ] **Step 5: SVG grafu — etykieta**

`RelationGraph.svelte` — `<svg viewBox=…>` dostaje `role="img"` i `aria-label`. Komponent zna centralną postać (sprawdź props — jeśli brak nazwy, użyj stałej):

```svelte
	<svg
		viewBox="0 0 {W} {H}"
		role="img"
		aria-label="Relation graph"
		class="w-full max-w-md rounded-xl border border-rule bg-surface"
	>
```

- [ ] **Step 6: Check + smoke**

Run: `npm run check && npm run lint`
Expected: 0 errors. Smoke: dropdown user menu otwiera/zamyka się, taby na `/shelf` działają, Escape zamyka dialog delete.

- [ ] **Step 7: Commit**

```bash
git add src/lib/components/ src/routes/
git commit -m "fix: a11y for dropdown, dialog, tabs, svg"
```

---

### Task 13: Infra — parytet prod po M13 (I1)

**Files:**
- Modify: `infra/compose/docker-compose.prod.yml`
- Modify: `infra/caddy/Caddyfile`
- Modify: `infra/.env.example`

- [ ] **Step 1: redis + celery + restart w prod compose**

W `docker-compose.prod.yml`:
- do serwisu `django` (po `command:`/`healthcheck:`) dodaj `restart: unless-stopped` oraz do `environment:` dwie linie:

```yaml
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
```

- po serwisie `django` dodaj:

```yaml
  celery:
    image: ghcr.io/stokuj/storyshelf-django:main
    container_name: storyshelf-celery
    env_file:
      - ../.env
    environment:
      DJANGO_ENV: prod
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      DATABASE_URL: postgres://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-secret-key}@db:5432/${POSTGRES_DB:-booksdb}
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
    volumes:
      - media:/app/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    command: celery -A config worker --loglevel=info --concurrency=4

  redis:
    image: redis:7
    container_name: storyshelf-redis
    restart: unless-stopped
```

(redis bez `ports:` — w prodzie tylko sieć wewnętrzna.)

- [ ] **Step 2: Caddyfile — media + static**

W `infra/caddy/Caddyfile` po bloku `handle /admin/*` dodaj (PRZED catch-all `handle {`):

```caddy
	# Django-served user uploads and collected static (admin, DRF, Swagger UI)
	handle /media/* {
		reverse_proxy django:8000
	}

	handle /static/* {
		reverse_proxy django:8000
	}
```

Django z `DEBUG=False` nie serwuje `/media/` ani `/static/` (helper `static()` no-opuje poza DEBUG) — proxy w Caddy musi mieć cel. W `backend-django/config/urls.py` zmień końcówkę pliku:

```python
# było:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ma być:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Prod: gunicorn serves uploads + collected static behind Caddy's
    # /media/* and /static/* handles (single-instance scale, no CDN).
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]
```

z importami: `from django.urls import include, path, re_path` (rozszerzenie istniejącego) i `from django.views.static import serve`.

- [ ] **Step 3: .env.example**

Po sekcji OpenRouter (linia 24) dodaj:

```bash
# Celery (M13 — AI character generation; service names from docker compose)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Throttling overrides (optional; defaults in config/settings/base.py)
# THROTTLE_AUTH_LOGIN=10/min
# THROTTLE_AUTH_REGISTER=5/hour
# THROTTLE_AUTH_REFRESH=30/min
# THROTTLE_CHARACTER_GENERATE=10/hour
```

- [ ] **Step 4: Walidacja**

Run: `docker compose -f infra/compose/docker-compose.prod.yml --env-file infra/.env config -q && echo OK`
Expected: `OK` (bez warningów o brakujących zmiennych poza DOMAIN itp., które mają defaulty/są w .env).

- [ ] **Step 5: Commit**

```bash
git add infra/ backend-django/config/urls.py
git commit -m "feat: redis+celery in prod compose"
```

---

### Task 14: Tooling — make verify z hosta + dockerignore + martwy setting (I3, N6)

**Files:**
- Modify: `Makefile`
- Create: `svelte-frontend/.dockerignore`
- Modify: `backend-django/.dockerignore`
- Modify: `backend-django/config/settings/base.py:171`
- Modify: `CLAUDE.md` (notka o dev-DB)

- [ ] **Step 1: Makefile — VERIFY_DATABASE_URL**

Po linii 7 (`PROD_COMPOSE = …`) dodaj:

```make
# make verify runs backend tests from the host; the dev DB listens on localhost.
# POSTGRES_* come from infra/.env (clean KEY=VALUE lines parse fine in make).
-include $(ENV_FILE)
VERIFY_DATABASE_URL ?= postgres://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@localhost:5432/$(POSTGRES_DB)
```

W targecie `verify` zmień dwie linie testowe:

```make
	cd $(ROOT_DIR)backend-django && DJANGO_ENV=dev DATABASE_URL=$(VERIFY_DATABASE_URL) uv run python -m pytest
	cd $(ROOT_DIR)backend-django && DJANGO_ENV=dev DATABASE_URL=$(VERIFY_DATABASE_URL) uv run python manage.py test config.tests.test_openapi_schema --noinput
```

- [ ] **Step 2: svelte-frontend/.dockerignore (nowy plik)**

```
node_modules/
.svelte-kit/
build/
e2e/
test-results/
playwright-report/
.env
.env.*
```

- [ ] **Step 3: backend-django/.dockerignore — rozszerz**

```
.venv/
**/__pycache__/
*.pyc
.git/
.gitignore
media/
.pytest_cache/
htmlcov/
```

- [ ] **Step 4: Usuń martwy CELERY_WORKER_CONCURRENCY**

`config/settings/base.py:171` — usuń linię `CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))` (compose podaje `--concurrency=4` w CLI; setting nigdy nie działał).

- [ ] **Step 5: CLAUDE.md — notka**

W sekcji „Komendy → Backend" po linii z pytest dodaj:

```markdown
> Testy z hosta wymagają żywej dev-DB (`make dev-up`); `make verify` ustawia `DATABASE_URL` sam.
```

- [ ] **Step 6: Weryfikacja end-to-end**

Run (z roota): `make verify`
Expected: wszystkie kroki przechodzą bez ręcznego env (ruff, check, pytest, openapi, svelte-check, lint).

- [ ] **Step 7: Commit**

```bash
git add Makefile svelte-frontend/.dockerignore backend-django/.dockerignore backend-django/config/settings/base.py CLAUDE.md
git commit -m "fix: make verify db url + dockerignore"
```

---

### Task 15: Testy backend — luki N1 (characters/feed/ratings)

**Files:**
- Modify: `backend-django/characters/tests/test_api.py`, `test_tasks.py`, `test_ai.py`
- Modify: `backend-django/feed/tests/test_api.py`
- Modify: `backend-django/ratings/tests/test_api.py`

(Testy re-dispatch DONE/FAILED/PENDING już dodane w Tasku 5.)

- [ ] **Step 1: characters — lista bez analizy + 404 detal**

Do `characters/tests/test_api.py` (klasa `CharacterApiTests`):

```python
    def test_list_without_analysis_returns_null_status(self):
        res = self.client.get(f"/api/books/{self.book.slug}/characters/")
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.data["status"])
        self.assertEqual(res.data["characters"], [])

    def test_detail_unknown_slug_returns_404(self):
        res = self.client.get(f"/api/books/{self.book.slug}/characters/ghost/")
        self.assertEqual(res.status_code, 404)
```

- [ ] **Step 2: tasks — asercja stanu RUNNING w trakcie**

Do `characters/tests/test_tasks.py` (klasa `GenerateTaskTests`):

```python
    def test_task_sets_running_before_generation(self):
        seen = []

        def capture(book):
            self.analysis.refresh_from_db()
            seen.append(self.analysis.status)
            return {"characters": [], "relations": []}

        with patch("characters.tasks.generate_characters", side_effect=capture):
            generate_characters_task(self.book.id)

        self.assertEqual(seen, [CharacterAnalysis.Status.RUNNING])
```

- [ ] **Step 3: ai — puste choices i nie-obiekt**

Do `characters/tests/test_ai.py` (klasa z `test_invalid_json_raises`):

```python
    def test_empty_choices_raises(self):
        body = json.dumps({"choices": []}).encode("utf-8")
        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            with self.assertRaises(CharacterGenerationError):
                generate_characters(FakeBook())

    def test_non_object_content_raises(self):
        body = json.dumps({"choices": [{"message": {"content": "[]"}}]}).encode("utf-8")
        with patch("characters.ai.urllib.request.urlopen", return_value=_MockResp(body)):
            with self.assertRaises(CharacterGenerationError):
                generate_characters(FakeBook())
```

- [ ] **Step 4: feed — zły cursor + kształt itemu**

Do `feed/tests/test_api.py` (klasa `FeedAPITest`):

```python
    def test_invalid_before_returns_400(self):
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL, {"before": "not-a-datetime"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_feed_item_shape(self):
        Review.objects.create(user=self.pub, book=self.book, body="great")
        self.client.force_authenticate(self.me)
        resp = self.client.get(FEED_URL)
        item = resp.data["results"][0]
        self.assertEqual(item["type"], "review")
        self.assertEqual(item["book"]["slug"], "b")
        self.assertEqual(item["body"], "great")
        self.assertIn("timestamp", item)
        self.assertEqual(item["actor"]["handle"], "pub")
```

- [ ] **Step 5: ratings — DELETE cudzej oceny → 404**

Do `ratings/tests/test_api.py` (klasa `RatingAPITest`, wzorzec z `shelf/tests/test_api.py:151-156`):

```python
    def test_delete_other_users_rating_returns_404(self):
        rating = Rating.objects.create(user=self.user_b, book=self.book, rating=5)
        self.client.force_authenticate(self.user)
        resp = self.client.delete(f"{URL}{rating.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Rating.objects.filter(id=rating.id).exists())
```

- [ ] **Step 6: Wszystko zielone**

Run: `DJANGO_ENV=dev DATABASE_URL=... uv run python -m pytest characters/ feed/ ratings/ -q` a potem pełny `uv run python -m pytest -q`
Expected: PASS (≈398). Te testy dokumentują istniejące zachowanie — jeśli któryś FAILUJE, to znaleziony bug: zatrzymaj się i zgłoś zamiast naginać asercje.

- [ ] **Step 7: Commit**

```bash
git add characters/ feed/ ratings/
git commit -m "test: cover characters feed ratings gaps"
```

---

### Task 16: E2E — seed The Hobbit i The Two Towers (I5)

**Files:**
- Modify: `svelte-frontend/e2e/global-setup.ts`

- [ ] **Step 1: Interface + wpisy**

Do interfejsu `SeedBook` dodaj pole:

```ts
	page_count?: number;
```

Do tablicy `BOOK_SEED` dopisz (po wpisie `1984`):

```ts
	{
		title: 'The Hobbit',
		year: 1937,
		description:
			'Bilbo Baggins, a comfort-loving hobbit, is swept into an epic quest to reclaim the Lonely Mountain from the dragon Smaug.',
		cover_url: 'https://covers.openlibrary.org/b/id/14627509-L.jpg',
		authors: ['J.R.R. Tolkien'],
		genres: ['Fantasy'],
		tags: ['classic'],
		page_count: 423,
		avg_rating: 4.4
	},
	{
		title: 'The Two Towers',
		year: 1954,
		description:
			'The second volume of The Lord of the Rings. The Fellowship is broken; Frodo and Sam continue toward Mordor.',
		cover_url: 'https://covers.openlibrary.org/b/id/8474036-L.jpg',
		authors: ['J.R.R. Tolkien'],
		genres: ['Fantasy'],
		tags: ['classic', 'epic'],
		avg_rating: 4.4
	}
```

(Sluggify: „The Hobbit" → `the-hobbit`, „The Two Towers" → `the-two-towers` — zgodnie ze stałymi w `shelf-status.spec.ts:12-15` i `reviews.spec.ts:8`. `page_count: 423` jest asertowane w `shelf-status.spec.ts:121`. Seeding jest idempotentny — istniejące tytuły są pomijane po `?search=`.)

- [ ] **Step 2: Przebieg E2E**

Run (z `svelte-frontend/`, dev stack żywy): `npx playwright test shelf-status reviews`
Expected: PASS. Jeśli throttle rejestracji (5/h) blokuje: `docker restart storyshelf-django` i powtórz.

- [ ] **Step 3: Commit**

```bash
git add e2e/global-setup.ts
git commit -m "test: seed hobbit and two towers in e2e"
```

---

### Task 17: Docs sync (I4)

**Files:**
- Modify: `CLAUDE.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/decisions/ADR-001-jwt-httponly-cookies.md`, `docs/decisions/ADR-003-celery-redis-llm.md`, `docs/api/README.md`

- [ ] **Step 1: CLAUDE.md**

- Linia 7: `Django 6 REST API + SvelteKit 2 SSR, Docker Compose. Bez AI/Celery — 3 kontenery (db, django, svelte).` → `Django 6 REST API + SvelteKit 2 SSR, Docker Compose. Od M13 AI (karty postaci): Celery + Redis + OpenRouter — 5 kontenerów (db, django, celery, redis, svelte).`
- Sekcja Layout: `apps: books, library, users, ratings, shelf, reviews, config` → `apps: books, library, users, ratings, shelf, reviews, feed, characters, config`
- Komentarz przy dev-up: `make dev-up          # db, django, svelte` → `make dev-up          # db, django, celery, redis, svelte`

- [ ] **Step 2: ROADMAP.md**

- Sekcja „Aktualny krok": zastąp treść opisem stanu — M13 zmergowane (PR #77), M14 zmergowane (PR #78), brak aktywnego milestone; wykonany holistyczny audyt + fixy (ta gałąź); następna decyzja: wdrożenie produkcyjne lub kolejny milestone (osobny `/brainstorming`).
- Tabela „Zrobione": wiersz M13 — `✅ na gałęzi feat/m13-ai-characters` → `✅ zmergowane do main (PR #77)`. Dodaj wiersz:

```markdown
| M14 Typed character relations | Enum `RelationType` (~20 typów / 7 grup) zamiast free-text `label`, unique (from, to, type), kolorowy ego-graf z pigułkami i legendą, hardening walidacji LLM | ✅ zmergowane do main (PR #78) |
```

- Sekcja „W toku": zaktualizuj — M13 nie czeka już na PR.
- `## Następne` / „Po M11–M13:" → „Po M11–M14:"; do punktu wdrożenia dopisz: `ALLOWED_HOSTS z domeną prod, non-root user w Dockerfile'ach, weryfikacja /media/ i /static/ przez Caddy`.
- „Kiedyś": w pozycji AI usuń „karty postaci, graf relacji" (zostaje: tematy/ton, pgvector itd. — zrobione odnotuj nawiasem); linia o homepage: `naturalny kandydat na M14 po M11–M13` → `naturalny kandydat na kolejny milestone`; dopisz pozycję: `Edycja bio z UI (PATCH /users/me/ wspiera bio; brak formularza)`.

- [ ] **Step 3: ARCHITECTURE.md**

- Nagłówek `## API surface (M1–M13; M7 admin-import odłożone)` → `(M1–M14; M7 admin-import odłożone)`.
- Do listy API dodaj (sekcja users):

```
/api/users/           lista publicznych profili (paginacja, ?search=, ?ordering=)
/api/u/{handle}/shelf/    publiczna domyślna półka (bramkowane profile_public)
```

- Diagram modeli: `CharacterRelation (from/to)` → `CharacterRelation (from/to, relation_type)`; `ShelfEntry (user+book, status, current_page)` → `ShelfEntry (user+book, status, current_page, finished_at)`; `Book (… avg_rating)` → dopisz `ratings_count`.
- Opis User: `avatar_url` → `avatar`.
- Sekcja kontenerów: zaktualizuj opis — redis+celery są w dev i prod compose (po Task 13); usuń/zmień zdanie „M13 dodaje…" na stan faktyczny.

- [ ] **Step 4: ADR-001 i ADR-003**

- ADR-001: obie wystąpienia `path=/api/users/token/refresh/` i `POST /api/users/token/refresh/` → `/api/auth/refresh/`.
- ADR-003 (linie 27–29): zdanie „Rate-limit/throttle generacji odłożony na później." → „Throttle wdrożony: scope `character_generate` 10/h per user (commit f524d53), konfigurowalny env `THROTTLE_CHARACTER_GENERATE`."

- [ ] **Step 5: docs/api/README.md**

Sekcję „Konsumpcja (Phase 3.0+)" przepisz bez terminologii Phase: plik służy wyłącznie jako snapshot kontraktu pilnowany testem; generacja typów TS (`openapi-typescript`) — niezaimplementowana, ewentualnie „Kiedyś".

- [ ] **Step 6: Weryfikacja grep**

Run (z roota):
`grep -rn "auth/me\|token/refresh\|3 kontenery\|Phase 3.0\|M1–M13" CLAUDE.md docs/ --include=*.md | grep -v superpowers`
Expected: brak trafień (poza ewentualnym raportem audytu w specs/ — ignorowany przez filtr superpowers).

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md docs/
git commit -m "docs: sync after audit fixes"
```

---

### Task 18: Weryfikacja końcowa

- [ ] **Step 1: Pełny verify**

Run (z roota): `make verify`
Expected: ruff + check + pytest (≈398) + openapi + svelte-check (0 errors) + lint — wszystko zielone.

- [ ] **Step 2: E2E**

Run (z `svelte-frontend/`): `npx playwright test`
Expected: PASS (przy throttle: `docker restart storyshelf-django`).

- [ ] **Step 3: Smoke ręczny (dev)**

- `/settings`: zła zmiana hasła → toast błędu; zapis → „Saved"; brak paska siły hasła.
- `/settings/profile`: tylko switch „Public profile".
- `/discover?author=…`: chip + ×; load-more (request na `/api/...`).
- `/users`: działa; (błąd API trudno zasymulować — wystarczy brak regresji).
- `/books/{slug}`: sekcja postaci działa (status, karty).

- [ ] **Step 4: Raport końcowy**

Zbierz wyniki i przedstaw użytkownikowi do oceny (workflow: implementacja → review → poprawki). PUSH dopiero po wyraźnej zgodzie użytkownika.
