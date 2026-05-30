# Roadmapa StoryShelf

> Stan: 2026-05-29. Aktualizowane ręcznie. Nie automatyzowane.

---

## Aktualny krok (next action for any Claude session)

**Bieżący branch:** `fix/pre-m3-cleanup` (po merge → `main`)

**ZADANIE:** Rozpocznij M3 — Rating + Shelf.

```
git checkout -b phase/m3-rating-shelf
/subagent-driven-development  # wg docs/superpowers/plans/2026-05-29-m3-rating-shelf.md
```

Spec: `docs/superpowers/specs/2026-05-29-m3-rating-shelf-design.md`
Plan (jeden, pod równoległe pasy): `docs/superpowers/plans/2026-05-29-m3-rating-shelf.md`

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

## W toku

Brak. Wybór następnego etapu z "Następne".

**Decyzja 2026-05-25:** profil publiczny/prywatny — bool `profile_public`, bez 3-state friends/private.

## Następne (priorytetyzowane)

### M3 — Rating + Shelf (jeden skonsolidowany plan, pod równoległe pasy)

Spec: [m3-rating-shelf-design](superpowers/specs/2026-05-29-m3-rating-shelf-design.md) ·
Plan: [m3-rating-shelf](superpowers/plans/2026-05-29-m3-rating-shelf.md)

Struktura wykonania: **Grupa 0 (Foundation, seq)** → **A ratings-BE ∥ B shelf-BE ∥ C frontend** (rozłączne pliki) → **D integracja+E2E (seq)**.

| Pas | Zakres | Status |
|-----|--------|--------|
| 0 | Obie apki + modele + migracje + wiring (`INSTALLED_APPS`, urls) | plan ✅ |
| A | Rating API (`ratings/`, PUT-upsert, sygnał → avg_rating, GET user-scoped) | plan ✅ |
| B | ShelfEntry CRUD (status, current_page, user_rating via Subquery, `?book_slug`) | plan ✅ |
| C | Frontend: `/shelf` (3 zakładki), RatingStars/StatusDropdown/ProgressBar/ShelfBookCard/ShelfControl, link „Shelf" w navbarze, kontrolki na `/books/[slug]` | plan ✅ |
| D | Regen OpenAPI+typy, pełne testy, Playwright E2E (8 scenariuszy) | plan ✅ |

> Stare plany `2026-05-27-phase-3a..3e` zastąpione tym jednym (usunięte).

### M4 — Reviews (plany wymagają `/writing-plans`)

| # | Etap | Status |
|---|------|--------|
| 4a | Review API (CRUD, pagination, avg update) | spec potrzebny |
| 4b | Reviews frontend (`/books/[slug]` sekcja recenzji) | spec potrzebny |
| 4c | Reviews E2E tests | spec potrzebny |

### Dalej

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt, sekrety na VPS (DigitalOcean). Wymaga konfiguracji `CORS_ALLOWED_ORIGINS` i `JWT_COOKIE_DOMAIN`.
2. **M5 Custom shelves** — Shelf + ShelfMembership CRUD, publiczny widok `/u/[handle]/shelves/[slug]`

## Kiedyś (bez priorytetu)

- Rekomendacje (collaborative + content-based)
- System tagowania społecznościowego (tagi user-defined poza adminem)
- Importer książek z OpenLibrary / Goodreads
- PWA (krok przed natywnym mobile)
- Statystyki czytania per użytkownik (wykresy, time-on-shelf)
- Social: feed znajomych, recenzje publiczne, polubienia
- **Follow / obserwowanie userów** — nie ma w żadnym milestone MVP (M1–M5). Backend już istnieje (model `UserFollow`, endpointy follow/followers/following, sekcja w eksporcie danych), ale UI (przycisk Follow + liczniki na profilu) wycięte z M2 i odłożone na post-MVP.

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
