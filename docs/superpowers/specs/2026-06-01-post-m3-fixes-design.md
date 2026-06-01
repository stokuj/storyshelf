# Post-M3 Fixes — Design

> Status: spec. Branch: `fix/post-m3-settings-cleanup`. Data: 2026-06-01.

## Cel

Zlikwidować user stories urwane w pół (backend istnieje, brak wiringu frontu), usunąć martwy kod i ujednolicić kontrakt typów. Bez nowych funkcji poza zakresem M1–M3.

Źródło: audyt 3 subagentów (2026-06-01) — patrz memory `project-half-wired-user-stories`.

## Zakres

### A. Wiring urwanych funkcji (backend gotowy)

#### A1. Data Export
- **Problem:** `settings/data/+page.svelte` ma `<form action="?/export">`, ale brak `+page.server.ts`. Backend `DataExportView.post` (`users/views.py:275`, `POST /api/users/me/export/`) zwraca plik ZIP (`application/zip`, `Content-Disposition: attachment`).
- **Rozwiązanie:** nowy `routes/settings/data/export/+server.ts` — `GET` handler robi server-side `fetch` (POST) do `{serverApiBase}/users/me/export/` z forwardem cookies (wzorzec jak `logout/+page.server.ts`), przepuszcza body ZIP oraz nagłówki `Content-Type` i `Content-Disposition` do przeglądarki.
- W `+page.svelte`: zamiana formularza na `<a href="/settings/data/export" download>` (natywny download).
- Błąd (np. 401/500 z backendu): handler przepuszcza status backendu (z krótkim tekstem); przy nie-200 przeglądarka pokazuje odpowiedź zamiast pobierać plik. Bez dodatkowego UI błędu.

#### A2. Delete account
- **Problem:** `settings/data/+page.svelte` ma `<form action="?/delete">` bez `+page.server.ts`. Dialog prosi o wpisanie *handle*, a backend `UserMeView.delete` (`users/views.py:166`, `DELETE /api/users/me/`) wymaga `current_password` (`AccountDeleteSerializer`).
- **Rozwiązanie:**
  - Nowy `routes/settings/data/+page.server.ts`, akcja `delete`: czyta `current_password` z formularza → `DELETE {serverApiBase}/users/me/` (forward cookies). Przy 204: czyści cookies `access_token`/`refresh_token` i `redirect(303, '/')` (jak `logout`). Przy 403: `fail(403, { error })`.
  - W `+page.svelte`: dialog zbiera **hasło** (`name="current_password"`, `type="password"`) zamiast handle; `use:enhance`. Stan `deleteHandle` usunięty.

#### A3. Avatar upload
- **Problem:** `settings/+page.svelte:28-38` — ukryty `<input type="file">`, "Upload photo" tylko otwiera picker; brak `onchange`/submitu → akcja `?/avatar` (która istnieje) i backend `AvatarUploadView` (`users/views.py:241`) nigdy nie są wołane.
- **Rozwiązanie:** dodać do inputu `onchange={(e) => e.currentTarget.form?.requestSubmit()}`. Jedna linia; reszta działa.

#### A4. Reading progress (`current_page`)
- **Problem:** `ShelfBookCard.svelte:77` renderuje `ProgressBar` (read-only) dla statusu `reading`; nigdzie nie da się ustawić `current_page`, mimo że API client (`lib/api/shelf.ts`), typ `ShelfEntryUpdate` i backend PATCH to wspierają.
- **Rozwiązanie:** na `ShelfBookCard` przy statusie `reading` dodać edytowalny input liczbowy (zakres 0…`page_count`) obok ProgressBar; `onchange` → `updateShelfEntry(fetch, entry.id, { current_page })` z optymistyczną aktualizacją i toastem (wzorzec jak `ShelfControl`).

### B. Usunięcie martwego kodu

| Element | Akcja |
|---|---|
| `lib/schemas/settings.ts` | usunąć (0 importów; resztki AI: `ai_tone`, `cite_quotes`, `default_spoiler_limit`; 3-state `friends` visibility odrzucone w ADR) |
| `lib/schemas/user.ts` | usunąć (0 importów) |
| `zod` w `package.json` | usunąć z dependencies (po usunięciu schematów brak użyć) |
| `lib/types/api.generated.ts` | **usunąć sam plik**; skrypt `types:api` **zostaje**; dodać plik do `.gitignore` (wygenerowany artefakt nie wraca do repo) |
| `routes/api/__mock/[...rest]/+server.ts` + `lib/api/__fixtures__/` | usunąć (dev-only, nieużywane — nic nie kieruje na `/api/__mock`) |
| `BookPreviewSerializer` (`books/serializers.py:10-21`) | usunąć (martwy; docstring opisuje nieistniejące endpointy) |
| Navbar Search (`AppShell.svelte:42`) | usunąć przycisk no-op (brak historyjki search w M1–M3) |

### C. Synchronizacja kontraktów typów użytkownika

Oba frontendowe typy użytkownika deklarują pola, których backend nie zwraca. Cel: typy = faktyczne odpowiedzi API; brak martwego/mylącego UI opartego na nieistniejących polach.

#### C1. `UserMe` (`lib/api/user.ts`)
- `UserMeSerializer` (`users/serializers.py:79-90`) zwraca: `id, handle, display_name, email, bio, avatar_url, member_since, profile_public`.
- Z typu `UserMe` usunąć pola nieistniejące/nieużywane: `email_verified`, `joined_at`, `followers_count`, `following_count` (follow = post-MVP). Zostają: `id, handle, display_name, email, bio, avatar_url`. (`member_since`/`profile_public` niekonsumowane przez consumerów `UserMe` — nie dodajemy, YAGNI.)

#### C2. Martwy blok „email verified" (`settings/+page.svelte:71-75`)
- Karta Email pokazuje `{#if user?.email_verified}` „✓ Verified" / „Not verified. Check your inbox." Backend nie zwraca `email_verified` i nie ma funkcji weryfikacji e-maila → blok zawsze pokazuje „Not verified" (mylące, martwe).
- Usunąć cały blok `{#if user?.email_verified}…{/if}` (wraz z usunięciem pola z `UserMe` w C1 — inaczej zostałoby odwołanie do nieistniejącego pola).

#### C3. `User` (`lib/types/user.ts`, przez barrel `$lib/types`)
- Używany jako typ odpowiedzi **profilu publicznego** (`routes/u/[handle]/+page.server.ts:7` → `apiFetch<User>`). `UserProfileSerializer` zwraca: `handle, display_name, bio, avatar_url, member_since, profile_public`.
- Szablon `u/[handle]/+page.svelte` konsumuje: `handle, display_name, bio, avatar_url, member_since`.
- Z typu `User` usunąć `id`, `email`, `email_verified` (publiczny endpoint ich nie zwraca). Zostają: `handle, display_name, bio, avatar_url, member_since`; dodać `profile_public: boolean` dla zgodności z serializerem. `UserId` (alias `number`) — sprawdzić użycia; usunąć jeśli osierocony po zmianie.

## Poza zakresem (świadomie)
- Follow UI — post-MVP wg ROADMAP; endpointy backendu zostają bez UI.
- Nieużywane prymitywy shadcn (`dialog`, `tabs`, `command`…) — biblioteczny kit UI, zostają.
- Wykorzystanie `api.generated.ts` jako źródła typów — osobny temat.

## Testy / weryfikacja
- E2E `settings.spec.ts`: export (link pobiera plik / odpowiedni status), delete (hasło → redirect na `/`), avatar (zmiana wysyła), `current_page` (ustawienie aktualizuje postęp).
- Backend: `DataExportView`/`UserMeView.delete`/`AvatarUploadView` już mają testy — zweryfikować, że nie dotykamy ich kontraktu.
- Bramki: `npm run check`, `npm run lint`, `DJANGO_ENV=dev uv run python manage.py test` — zielone.

## Kryteria sukcesu
1. Każda funkcja A1–A4 działa end-to-end z poziomu UI.
2. Zero martwego kodu z listy B w repo; `zod` usunięty z deps; lint czysty.
3. Typy `UserMe` i `User` zgodne z odpowiedziami backendu; brak UI opartego na nieistniejących polach (`email_verified`).
4. Wszystkie bramki testowe zielone.
