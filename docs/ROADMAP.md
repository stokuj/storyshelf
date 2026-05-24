# Roadmapa StoryShelf

> Stan: 2026-05-24. Aktualizowane ręcznie. Nie automatyzowane.

---

## 🎯 Aktualny krok (next action for any Claude session)

**Bieżący branch:** `main` (czysty)

**ZADANIE:** Rozpocznij Phase 2.7 — Svelte foundation.

```
git checkout -b phase/2.7-svelte-foundation
/executing-plans  # lub ręcznie wg svelte(wideframe)/handoff/prompts/01-04
```

Handoff prompts: `svelte(wideframe)/handoff/prompts/01-setup.md` … `04-discover.md`

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

## W toku

**Phase 2 — Implementacja frontendu SvelteKit** ([Issue #46](https://github.com/stokuj/storyshelf//issues/46))

Sub-etapy pozostałe do implementacji:

| # | Etap | Branch | Status |
|---|------|--------|--------|
| 2.3 | Multi-shelf collections (Shelf + ShelfMembership, public shelves endpoint) | `phase/2.3-shelves` | spec ✅, plan ✅ — niezweryfikowane w kodzie |
| 2.4 | Account management (PATCH /password, /email, multipart avatar + ImageField, GDPR export + DELETE) | `phase/2.4-account` | spec ✅, plan ✅ — niezweryfikowane w kodzie |
| **2.7** | **Svelte foundation (prompts 01-04)** | `phase/2.7-svelte-foundation` | **← NASTĘPNY** |
| 2.8 | Svelte books + characters + AI panel (prompts 05-07) | `phase/2.8-svelte-books` | — |
| 2.9 | Svelte profile + settings + polish (prompts 08, 09, 11) | `phase/2.9-svelte-profile` | — |

**Decyzje grilling-sessions z 2026-05-23** (źródło: rozmowa wokół `svelte(wideframe)/handoff/`):

- Cross-book Character WYCIĘTE z MVP (ADR-003 zachowane); manualne merge w adminie jako Faza 3
- AI chat (SSE "Ask about this book") WYCIĘTE z MVP — wymagałoby złamania ADR-002 (text retention) + ASGI
- Verify/reject AI characters WYCIĘTE z MVP; zostaje minimalny `POST /books/:id/characters/:id/hide` (admin, soft-delete)
- Spoiler control WYCIĘTE (wymagałoby chapter-aware chunking)
- AI extract endpoint hardcoded `IsAdminUser` (otwarcie userom = osobna decyzja w Fazie 3 z rate-limitem)
- Visibility profilu: bool (`profile_public`), bez 3-state friends/private
- Activity feed WYCIĘTY (zamiast tego "Recently read" 6 covers)
- Vue umiera w Phase 2.6, brak okresu przejściowego — API zmiany nie wymagają wstecznej kompatybilności

**Workflow:** plan frontendu Svelte (`svelte(wideframe)/handoff/`) → analiza → backend extensions (2.0-2.5) → Vue removal (2.6) → Svelte implementation (2.7-2.9).

## Następne (priorytetyzowane)

> Etapy po zakończeniu Phase 2. Kolejność do rewizji po Phase 2.

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt zamiast `tls internal`, sekrety na VPS (DigitalOcean). Wymaga konfiguracji `CORS_ALLOWED_ORIGINS` i `JWT_COOKIE_DOMAIN` per [Spec 2.0](superpowers/specs/2026-05-23-phase2.0-foundation.md).
2. **Phase 3 — End-to-end tests with Playwright** ([Issue #47](https://github.com/stokuj/storyshelf//issues/47))
3. **Phase 4 — AI/LLM pipeline expansion** ([Issue #48](https://github.com/stokuj/storyshelf//issues/48)) — m.in. AI chat z SSE (wycięte z Phase 2 MVP), cross-book Character disambiguation z LLM-assisted merge
4. **Idempotentność `analyse_book`** — wchodzi w skład Phase 2.2 (soft-delete `is_hidden` + stabilne slugi przy re-analyze)
5. **Manualny merge cross-book Character** w Django Admin — wymaga ADR-005 (nowy model `Character` + M2M z BookCharacter)

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
