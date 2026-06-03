# Roadmapa StoryShelf

> Stan: 2026-06-03. Aktualizowane ręcznie. Nie automatyzowane.

---

## Aktualny krok (next action for any Claude session)

**Bieżący branch:** `feat/m6-follow-ui` (M6 zaimplementowane, czeka na PR/merge; backend 297 testów, frontend check/lint clean, E2E follow zielone).

**ZADANIE:** Domknąć M6 (PR + merge), potem **M7 — Import książek z UI admina**. Każdy milestone = osobny `/brainstorming` → spec → plan → implementacja. Wdrożenie produkcyjne odłożone na po M10.

---

## Zrobione

| Etap | Zakres | Wynik |
|------|--------|-------|
| Migracja z Java Spring Boot | Backend przepisany na Django + DRF | `backend-django/`, legacy `backend/` usunięty |
| JWT przez HttpOnly cookies | Migracja z localStorage, `JWTCookieAuthentication`, silent refresh | [ADR-001](decisions/ADR-001-jwt-httponly-cookies.md) |
| Django audit fixes | validators, unique constraints, signals, lint config | — |
| SDD docs restructure | Wprowadzenie struktury `docs/` (ARCHITECTURE, ROADMAP, decisions/) + integracja z plugin superpowers | PR #43 |
| M1 Auth + profil | Register, login, profile/settings, public profile, follow | ✅ zmergowane do main |
| M2 Katalog książek | Books API (paginacja, slug, filtry/search/sort), SvelteKit frontend (/discover, /books/[slug]), E2E | ✅ zmergowane do main (PR #60) |
| PRE-M3 cleanup | Usunięcie AI/Celery kodu (analysis, reviews, shelf apps), uproszczenie infra do 3 kontenerów | ✅ branch fix/pre-m3-cleanup |
| M3 Rating + Shelf | `ratings/` (PUT-upsert, sygnał → avg_rating), `shelf/` (ShelfEntry CRUD, status, current_page), frontend `/shelf` + kontrolki na `/books/[slug]`, E2E | ✅ zmergowane do main (PR #62 + post-M3 fixes #63) |
| M4 Reviews | `reviews/` (Review = body, unique user+book, PUT-upsert, publiczna lista, `/me`, owner-only delete, `author_rating` z Rating via Subquery), eksport danych, frontend sekcja recenzji na `/books/[slug]` (LoadMore), E2E (4 scenariusze) | ✅ zmergowane do main (PR #64 + poprawki po review #65–#67) |
| M5 Custom shelves | `shelf/` (Shelf + ShelfMembership obok ShelfEntry; owner CRUD `/api/shelves/`, membership add/remove idempotentne, publiczny odczyt `/api/u/{handle}/shelves/` bramkowany `profile_public`), eksport danych, frontend (zakładka „Moje półki" na `/shelf`, `/shelf/[slug]`, kontrolka na `/books/[slug]`, publiczny `/u/[handle]/shelves/[slug]`), E2E (4 scenariusze) | ✅ zmergowane do main (PR #68) |
| Google Books import | `import_books` management command (CLI) — import po ISBN, dedup+update po `isbn`, `categories` → split na osobne `genres`, reuse `BookWriteSerializer`, stdlib `urllib` (zero nowych deps); `--file`, `--dry-run`; M2M (authors/genres/tags) zachowane gdy Google ich nie zwróci; testy z mockiem `urlopen` | ✅ zmergowane do main (PR #69) |
| Audyt + cleanup | Audyt dokumentacji/infra (subagenci), `.env`→`infra/`, Caddy/porty/ścieżki, fixy B1/S1/B2 + F1/F3, usunięcie dead code; usunięcie `.claude/` ze śledzenia remote | ✅ zmergowane do main (PR #70) |
| M6 Follow/obserwowanie (UI) | Profil: `followers_count`/`following_count`/`is_following` (annotacje + SerializerMethodField), `FollowUserSerializer` (wzbogacone listy), optymistyczny `FollowButton` (writable `$derived`, revert na realny błąd), klikalne liczniki, trasy `/u/[handle]/followers` i `/following` (`UserRow`/`FollowList`); E2E follow flow + gość-bez-przycisku; OpenAPI snapshot zregenerowany | ✅ zaimplementowane na `feat/m6-follow-ui` (czeka na PR/merge) |

## W toku

Brak. Wybór następnego etapu z "Następne".

**Decyzja 2026-05-25:** profil publiczny/prywatny — bool `profile_public`, bez 3-state friends/private.

**Decyzja 2026-06-03:** faza post-MVP = M6–M10 (Follow UI, Admin import UI, dokończenie half-wired stories, statystyki czytania, audyt/cleanup). Każdy milestone osobna specka. Wdrożenie produkcyjne dopiero po M10.

## Następne (priorytetyzowane)

> Każdy milestone: osobny `/brainstorming` → spec w `docs/superpowers/specs/` → plan → implementacja na własnej gałęzi → PR. Kolejność wiążąca.

| Milestone | Zakres | Gałąź |
|-----------|--------|-------|
| **M7 — Import książek z UI admina** (A2) | Panel w aplikacji do importu po ISBN (dziś tylko CLI `import_books`/`docker exec`). Reuse istniejącej logiki importu; dostęp admin-only. | `feat/m7-admin-import-ui` |
| **M8 — Dokończenie half-wired stories** (A3) | Wiring frontu dla gotowego backendu: eksport danych (download), upload avatara, `current_page` jako progress czytania. | `feat/m8-wire-user-stories` |
| **M9 — Statystyki czytania** (B1) | Agregacje w API + frontend: książki/rok, rozkład ocen, time-on-shelf, wykresy per użytkownik. Moduł samodzielny, bez zależności od social. | `feat/m9-reading-stats` |
| **M10 — Audyt / fix / cleanup** | Osobna faza porządkowa po M6–M9: audyt subagentami (dead code, dokumentacja, infra), poprawki, aktualizacja `ARCHITECTURE.md`/`ROADMAP.md`. | `chore/m10-audit-cleanup` |

Po M10:

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt, sekrety na VPS (DigitalOcean). Wymaga konfiguracji `CORS_ALLOWED_ORIGINS` i `JWT_COOKIE_DOMAIN`.

## Kiedyś (bez priorytetu)

- Rekomendacje (collaborative + content-based)
- System tagowania społecznościowego (tagi user-defined poza adminem)
- Importer książek z OpenLibrary / Goodreads (CSV z Goodreads, ISBN→OpenLibrary; Google Books — zrobione, patrz „Zrobione")
- PWA (krok przed natywnym mobile)
- Social: feed znajomych, recenzje publiczne, polubienia (buduje na M6 Follow)
- Lista userów `/users` (browse/sort/search) + podgląd cudzej aktywności czytelniczej i domyślnej półki na profilu (`/u/[handle]/shelf`); profil prywatny niewidoczny na liście
- Spersonalizowana strona główna `/` (Continue reading, aktywność followowanych, rekomendacje; dla gości trending + opis apki) zamiast redirectu na `/discover`
- Rozszerzenia statystyk (po M9): reading streak (dni z rzędu), yearly wrap
- AI — analiza książek (karty postaci, graf relacji, tematy/ton; per-book LLM call + pgvector) — **poza MVP**, patrz „Czego NIE robimy"
- ML/DE do CV: semantic search + embeddingi (sentence-transformers + pgvector), pipeline analityczny w dbt, Character Knowledge Graph (NetworkX + LLM extraction)

## Czego NIE robimy

- **Skala >10k książek na jedną instancję** — projekt single-tenant, nie marketplace
- **Real-time collaboration** — żadnych live cursors, presence, edytora wspólnego
- **Native mobile (iOS/Android)** — PWA wystarczy
- **AI/LLM w MVP** — brak Celery, RabbitMQ, Redis; NLP/AI pipeline odłożone poza M5
- **Subskrypcje / płatności** — projekt hobbystyczny / portfoliowy

## Konwencja aktualizacji

- Nowy etap zaczyna się od `/brainstorming` → spec w `docs/superpowers/specs/`
- Po zakończeniu przesuwamy wpis z **W toku** do **Zrobione** + dopisujemy link do ADR (jeśli powstał)
- "Następne" przeglądamy raz na kilka etapów — kolejność może się zmieniać
- "Czego NIE robimy" jest **immutable jak ADR** — wykreślenie wymaga osobnego brainstormingu
