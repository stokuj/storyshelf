# Roadmapa StoryShelf

> Stan: 2026-05-22. Aktualizowane ręcznie. Nie automatyzowane.

## Zrobione

| Etap | Zakres | Wynik |
|------|--------|-------|
| Migracja z Java Spring Boot | Backend przepisany na Django + DRF | `backend-django/`, legacy `backend/` usunięty |
| NLP pipeline redesign | Zastąpienie Kafka → HTTP callbacks, 5 tasków → 2, BERT → spaCy CPU-only | Patrz [ADR-002](decisions/ADR-002-dwa-workery-celery.md), [ADR-003](decisions/ADR-003-encje-ner-per-book.md) |
| Encje per-book | Usunięcie modelu Chapter, `unique_together(name, book)` | [ADR-003](decisions/ADR-003-encje-ner-per-book.md) |
| JWT przez HttpOnly cookies | Migracja z localStorage, `JWTCookieAuthentication`, silent refresh | [ADR-001](decisions/ADR-001-jwt-httponly-cookies.md) |
| Frontend audit fixes | useAsyncState, AlertMessage, NotFoundState, router auth init | — |
| Django audit fixes | validators, unique constraints, signals, lint config | — |
| SDD docs restructure | Wprowadzenie 3-warstwowej dokumentacji + ADR + slash commands | Bieżący etap |

## W toku

Brak. Po zakończeniu restruktryzacji dokumentacji — wybór następnego etapu z "Następne".

## Następne (priorytetyzowane)

1. **Wdrożenie produkcyjne** — odkomentowanie deploy step w `.github/workflows/ci.yml`, Caddy z Let's Encrypt zamiast `tls internal`, sekrety na VPS (DigitalOcean).
2. **Idempotentność `analyse_book`** — obecnie re-upload tekstu akumuluje encje. Auto-delete starych `BookCharacter/Place/Organization` przed re-analizą.
3. **Disambiguation aliasów postaci** — "Frodo" vs "Frodo Baggins" vs "Mr. Baggins" w tej samej książce. Manual review w admin + auto-merge przez LLM.
4. **Search/filter w bibliotece** — filtrowanie po autorze, gatunku, tagu, ocenie, statusie półki. Backend ma endpointy, frontend nie wykorzystuje.

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
