# Roadmapa StoryShelf

> Stan: 2026-05-23. Aktualizowane ręcznie. Nie automatyzowane.

---

## 🎯 Aktualny krok (next action for any Claude session)

**Bieżący branch:** `phase/2.0-foundation` (3 commity ahead of main, wypchnięte na origin)

**ZADANIE:** Napisać 6 specyfikacji dla sub-faz Phase 2.1 – 2.6, **sekwencyjnie** (jedna po drugiej, nie równolegle).

| # | Spec do napisania | Plik docelowy |
|---|---|---|
| 2.1 | Books API extensions | `docs/superpowers/specs/2026-05-23-phase2.1-books-api.md` |
| 2.2 | AI extraction API | `docs/superpowers/specs/2026-05-23-phase2.2-ai-extraction.md` |
| 2.3 | Multi-shelf collections | `docs/superpowers/specs/2026-05-23-phase2.3-shelves.md` |
| 2.4 | Account management | `docs/superpowers/specs/2026-05-23-phase2.4-account.md` |
| 2.5 | Character disambiguation | `docs/superpowers/specs/2026-05-23-phase2.5-disambiguation.md` |
| 2.6 | Vue removal + SvelteKit setup | `docs/superpowers/specs/2026-05-23-phase2.6-svelte-setup.md` |

**Wzór stylu:** [`docs/superpowers/specs/2026-05-23-phase2.0-foundation.md`](superpowers/specs/2026-05-23-phase2.0-foundation.md) — zachowaj strukturę (Kontekst, Obszar 1/2/3..., Pliki do zmiany, Akceptacja, Out of scope).

**Source decyzji:** sekcja "Decyzje grilling-sessions z 2026-05-23" niżej w tym pliku + handoff w `svelte(wideframe)/handoff/03-api-contract.md` (kontrakt API którego frontend wymaga).

**Workflow:**
1. Każdy spec piszesz w osobnym subagencie (`Agent` tool, `model: sonnet` lub `opus` — sonnet z 1M kontekstem wymaga `/usage-credits`, sonnet ze standardem nie; opus zawsze działa).
2. Po każdym specu — commit na bieżącym branchu (`docs(phase-2.X): spec for ...`).
3. Po wszystkich 6 — pchnij na origin i kontynuuj decyzję czy plans piszemy teraz (batch) czy JIT przed implementacją każdej sub-fazy.

**Wytyczne dla subagenta (do każdego spec promptu):**
- Przeczytaj wzór `phase2.0-foundation.md` przed pisaniem
- Przeczytaj odpowiednie pliki backendu pod kątem stanu obecnego (konkrety: `plik:linia`)
- Zaczerpnij decyzje z sekcji "Decyzje grilling-sessions" niżej
- Cięcia z MVP wypisz explicitnie w "Out of scope" żeby agent implementacji nie nadinterpretował
- Po polsku komentarze i opisy, kod po angielsku
- Wróć z 3-zdaniowym raportem (ile obszarów, co zauważyłeś w trakcie, czy zakres mieści się w jednym PR)

**Stan zaawansowania zadania (zaktualizuj po każdym specu):**
- [ ] 2.1 Books API extensions
- [ ] 2.2 AI extraction API
- [ ] 2.3 Multi-shelf collections
- [ ] 2.4 Account management
- [ ] 2.5 Character disambiguation
- [ ] 2.6 Vue removal + SvelteKit setup

Po zakończeniu wszystkich 6: usuń tę sekcję "Aktualny krok" i podejmij decyzję o dalszych krokach z użytkownikiem.

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
| SDD docs restructure | Wprowadzenie struktury `docs/` (ARCHITECTURE, ROADMAP, decisions/) + integracja z plugin superpowers (`/brainstorming` → `/writing-plans` → `/executing-plans` → PR) | PR #43 |

## W toku

**Phase 2 — Migracja frontendu Vue 3 → SvelteKit** ([Issue #46](https://github.com/stokuj/storyshelf//issues/46))

Etap 2.0 (Foundation) — spec + plan gotowe, czeka na implementację:
- Spec: [`docs/superpowers/specs/2026-05-23-phase2.0-foundation.md`](superpowers/specs/2026-05-23-phase2.0-foundation.md)
- Plan: [`docs/superpowers/plans/2026-05-23-phase2.0-foundation.md`](superpowers/plans/2026-05-23-phase2.0-foundation.md)

Sub-etapy Phase 2 (kolejność wykonania):

| # | Etap | Branch | Status |
|---|------|--------|--------|
| 2.0 | Foundation (OpenAPI snapshot, CORS+cookies cross-origin, ADR Vue removal) | `phase/2.0-foundation` | spec ✅, plan ✅ |
| 2.1 | Books API extensions (paginacja, slug, genre/sort, contains-character, scoped reviews) | `phase/2.1-books-api` | spec ⏳ |
| 2.2 | AI extraction API (endpointy admin-gated, `source`+`confidence`+`slug` na BookCharacter, `ai_extraction_status` na Book, soft-delete `is_hidden`, idempotentność) | `phase/2.2-ai-extraction` | spec ⏳ |
| 2.3 | Multi-shelf collections (Shelf + ShelfMembership, public shelves endpoint) | `phase/2.3-shelves` | spec ⏳ |
| 2.4 | Account management (PATCH /password, /email, multipart avatar + ImageField, GDPR export + DELETE) | `phase/2.4-account` | spec ⏳ |
| 2.5 | Character disambiguation (alias merge w obrębie książki — zastępuje stary roadmap pkt 3) | `phase/2.5-disambiguation` | spec ⏳ |
| 2.6 | Vue removal + SvelteKit setup (zgodnie z ADR-004) | `phase/2.6-svelte-setup` | spec ⏳ |
| 2.7 | Svelte foundation (prompts 01-04 z `svelte(wideframe)/handoff/prompts/`) | `phase/2.7-svelte-foundation` | — |
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
