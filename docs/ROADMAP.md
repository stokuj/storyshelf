# Roadmapa StoryShelf

> Stan: 2026-06-01. Aktualizowane ręcznie. Nie automatyzowane.

---

## Aktualny krok (next action for any Claude session)

**Bieżący branch:** `phase/m4-reviews` (gotowy do merge → `main`)

**ZADANIE:** Po merge M4 — wybór następnego etapu z "Następne" (wdrożenie prod / M5 Custom shelves).

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
| M4 Reviews | `reviews/` (Review = body, unique user+book, PUT-upsert, publiczna lista, `/me`, owner-only delete, `author_rating` z Rating via Subquery), eksport danych, frontend sekcja recenzji na `/books/[slug]` (LoadMore), E2E (4 scenariusze) | ✅ branch phase/m4-reviews (243/243 backend, E2E 4/4) |

## W toku

Brak. Wybór następnego etapu z "Następne".

**Decyzja 2026-05-25:** profil publiczny/prywatny — bool `profile_public`, bez 3-state friends/private.

## Następne (priorytetyzowane)

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
