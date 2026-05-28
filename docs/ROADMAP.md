# Roadmapa StoryShelf

> Stan: 2026-05-28. Aktualizowane ręcznie. Nie automatyzowane.

---

## 🎯 Aktualny krok (next action for any Claude session)

**Bieżący branch:** `main` (czysty, M2 zmergowane)

**ZADANIE:** Rozpocznij M3 — Rating + Shelf.

```
git checkout -b phase/m3-rating-shelf
/subagent-driven-development  # wg planów docs/superpowers/plans/2026-05-27-phase-3a..3e
```

Plany: `docs/superpowers/plans/2026-05-27-phase-3a-rating-api.md` … `phase-3e-rating-widget.md`

---

## Zrobione

| Etap | Zakres | Wynik |
|------|--------|-------|
| Migracja z Java Spring Boot | Backend przepisany na Django + DRF | `backend-django/`, legacy `backend/` usunięty |
| NLP pipeline redesign | Zastąpienie Kafka → HTTP callbacks, 5 tasków → 2, BERT → spaCy CPU-only | Patrz [ADR-002](decisions/ADR-002-dwa-workery-celery.md), [ADR-003](decisions/ADR-003-encje-ner-per-book.md) |
| Encje per-book | Usunięcie modelu Chapter, `unique_together(name, book)` | [ADR-003](decisions/ADR-003-encje-ner-per-book.md) |
| JWT przez HttpOnly cookies | Migracja z localStorage, `JWTCookieAuthentication`, silent refresh | [ADR-001](decisions/ADR-001-jwt-httponly-cookies.md) |
| Frontend audit fixes | useAsyncState, AlertMessage, NotFoundState, router auth init | — |
| Django audit fixes | validators, unique constraints, signals, lint config | — |
| SDD docs restructure | Wprowadzenie struktury `docs/` (ARCHITECTURE, ROADMAP, decisions/) + integracja z plugin superpowers | PR #43 |
| Phase 2.0 Foundation | OpenAPI snapshot, CORS+cookies cross-origin, ADR Vue removal | ✅ zmergowane do main |
| Phase 2.1 Books API | Paginacja, slug, genre/sort, contains-character, scoped reviews | ✅ zmergowane do main |
| Phase 2.2 AI extraction | Admin-gated endpointy, `source`+`confidence`+`slug`, `ai_extraction_status`, soft-delete `is_hidden` | ✅ zmergowane do main |
| Phase 2.5 Disambiguation | Alias merge w obrębie książki | ✅ zmergowane do main |
| Phase 2.6 Vue removal + SvelteKit setup | Vue usunięty, SvelteKit zainstalowany (szkielet routes) | ✅ zmergowane do main |
| Phase 2.7 Svelte foundation | AppShell, atomy, typy, API wrappery, mock fixtures, `/discover` | ✅ zmergowane do main |
| Phase 2.8 Svelte books + characters + AI | `/books/[slug]`, AICastPanel, RelationGraph, character pages | ✅ zmergowane do main |
| Phase 2.9 Svelte profile + settings + polish | `/u/[handle]`, `/settings/*`, login/signup, a11y, meta | ✅ zmergowane do main |
| M2 Catalog milestone (E2E + bugfixy) | Playwright E2E, dropdown fix, getApiBase SSR, RabbitMQ fix, shelf/profile | ✅ zmergowane do main (PR #60) |

## W toku

Brak. Wybór następnego etapu z "Następne".

**Decyzja 2026-05-25:** profil ma dwie osobne sekcje shelf:
- **Recently read** — publiczna, 6 okładek, widoczna dla wszystkich (endpoint `/users/<handle>/recently-read/`)
- **My reading list** — prywatna, pełna lista ShelfEntry pogrupowana po statusach, widoczna tylko dla właściciela profilu (endpoint `/api/shelf/`)

**Decyzje grilling-sessions z 2026-05-23** (źródło: rozmowa wokół `svelte(wideframe)/handoff/`):

- Cross-book Character WYCIĘTE z MVP (ADR-003 zachowane); manualne merge w adminie jako Faza 3
- AI chat (SSE "Ask about this book") WYCIĘTE z MVP — wymagałoby złamania ADR-002 (text retention) + ASGI
- Verify/reject AI characters WYCIĘTE z MVP; zostaje minimalny `POST /books/:id/characters/:id/hide` (admin, soft-delete)
- Spoiler control WYCIĘTE (wymagałoby chapter-aware chunking)
- AI extract endpoint hardcoded `IsAdminUser` (otwarcie userom = osobna decyzja w Fazie 3 z rate-limitem)
- Visibility profilu: bool (`profile_public`), bez 3-state friends/private
- Activity feed WYCIĘTY (zamiast tego "Recently read" 6 covers)
- Vue umiera w Phase 2.6, brak okresu przejściowego — API zmiany nie wymagają wstecznej kompatybilności

## Następne (priorytetyzowane)

### M3 — Rating + Shelf (plany gotowe)

| # | Etap | Plan | Status |
|---|------|------|--------|
| 3a | Rating API (`ratings/` app, upsert, signal → avg_rating) | [phase-3a](superpowers/plans/2026-05-27-phase-3a-rating-api.md) | plan ✅ |
| 3b | ShelfEntry CRUD API (status, progress, user_rating via Subquery) | [phase-3b](superpowers/plans/2026-05-27-phase-3b-shelfentry-api.md) | plan ✅ |
| 3c | `/shelf` Frontend (tabs, inline actions, RatingStars, ProgressBar) | [phase-3c](superpowers/plans/2026-05-27-phase-3c-shelf-frontend.md) | plan ✅ |
| 3d | Shelf E2E tests (7 scenariuszy: tabs, status, rating, progress, cross-user) | [phase-3d](superpowers/plans/2026-05-27-phase-3d-e2e-shelf.md) | plan ✅ |
| 3e | RatingWidget na `/books/[slug]` (interaktywne gwiazdki + avg community) | [phase-3e](superpowers/plans/2026-05-27-phase-3e-rating-widget.md) | plan ✅ |

### M4 — Reviews (plany wymagają `/writing-plans`)

| # | Etap | Status |
|---|------|--------|
| 4a | Review API (CRUD, pagination, avg update) | spec potrzebny |
| 4b | Reviews frontend (`/books/[slug]` sekcja recenzji) | spec potrzebny |
| 4c | Reviews E2E tests | spec potrzebny |

### Dalej

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt zamiast `tls internal`, sekrety na VPS (DigitalOcean). Wymaga konfiguracji `CORS_ALLOWED_ORIGINS` i `JWT_COOKIE_DOMAIN` per [Spec 2.0](superpowers/specs/2026-05-23-phase2.0-foundation.md).
2. **AI/LLM pipeline expansion** — AI chat z SSE (wycięte z Phase 2 MVP), cross-book Character disambiguation z LLM-assisted merge
3. **Idempotentność `analyse_book`** — soft-delete `is_hidden` + stabilne slugi przy re-analyze
4. **Manualny merge cross-book Character** w Django Admin — wymaga ADR-005 (nowy model `Character` + M2M z BookCharacter)

## Kiedyś (bez priorytetu)

- Rekomendacje (collaborative + content-based z encji NER jako features)
- System tagowania społecznościowego (tagi user-defined poza adminem)
- Importer książek z OpenLibrary / Goodreads
- PWA (krok przed natywnym mobile)
- Statystyki czytania per użytkownik (wykresy, time-on-shelf)
- Social: feed znajomych, recenzje publiczne, polubienia

## Czego NIE robimy

- **Skala >10k książek na jedną instancję** — projekt single-tenant, nie marketplace
- **Real-time collaboration** — żadnych live cursors, presence, edytora wspólnego
- **Native mobile (iOS/Android)** — PWA wystarczy
- **Custom LLM training/fine-tuning** — używamy OpenRouter, nie hostujemy modeli
- **Pełnotekstowe wyszukiwanie po treści książek** — `Book.text` jest tymczasowe (czyszczone po NLP)
- **Subskrypcje / płatności** — projekt hobbystyczny / portfoliowy

## Konwencja aktualizacji

- Nowy etap zaczyna się od `/brainstorming` → spec w `docs/superpowers/specs/`
- Po zakończeniu przesuwamy wpis z **W toku** do **Zrobione** + dopisujemy link do ADR (jeśli powstał)
- "Następne" przeglądamy raz na kilka etapów — kolejność może się zmieniać
- "Czego NIE robimy" jest **immutable jak ADR** — wykreślenie wymaga osobnego brainstormingu
