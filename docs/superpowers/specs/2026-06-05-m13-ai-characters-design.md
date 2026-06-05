# M13 — AI Character Analysis (design)

> Data: 2026-06-05 · Gałąź: `feat/m13-ai-characters` · Status: spec

## Cel

Pod książką sekcja z **postaciami** (karty z monogramem, jak siatka w discovery), klik w postać →
podstrona z opisem i **grafem relacji**. Książki domyślnie nie mają analizy — zalogowany user
klika **„Generate AI"**, co odpala generację w tle (LLM z własnej wiedzy, bez pełnego tekstu książki).

To otwiera fazę AI projektu: pierwszy zewnętrzny provider LLM + przetwarzanie w tle (Celery + Redis).

## Decyzje (z brainstormingu)

| Temat | Decyzja |
|---|---|
| Karta postaci | Monogram (inicjały + kolor z imienia), brak zdjęć — LLM nie zwraca grafik |
| Graf relacji | Ego-graf (postać w środku, bezpośrednie relacje), ręczny SVG, węzły klikalne → podstrona danej postaci |
| Kto generuje | Każdy zalogowany user (zabezpieczenie/rate-limit **odłożone** — znane ryzyko) |
| Regeneracja | Dozwolona — nadpisuje poprzednią analizę |
| Limit postaci | Max 12 najistotniejszych |
| Provider | OpenRouter, model z env (`OPENROUTER_MODEL`), goły HTTP (bez LangChain) |
| Wykonanie | Async w tle — **nie** synchronicznie (sync = worker starvation przy wielu klikach) |
| Kolejka | Celery + Redis (broker + result backend); RabbitMQ odrzucone jako przerost |

### Znane ryzyko (świadomy dług)

„Każdy zalogowany user + regeneracja dozwolona" = otwarta furtka kosztowa. Zabezpieczenie (rate-limit
/ throttle / cap per user) **odłożone na później** — decyzja użytkownika. Jedyny bezpiecznik w v1:
idempotencja per książka (jeden job naraz) + bounded worker concurrency.

## Architektura

### Nowa app `characters/`

Feature jest book-scoped i większy (modele + task + klient AI) → osobna app, spójnie z `reviews/`, `feed/`.

### Model danych

```
CharacterAnalysis (OneToOne → Book)        # cykl życia generacji
  status: pending | running | done | failed
  error_message: str (blank)
  model: str                                # model z env użyty do generacji
  updated_at

Character (FK → Book, related_name="characters")
  name: str
  slug: SlugField                           # unique per (book, slug)
  role: str                                 # krótkie, np. "Protagonist"
  description: TextField                     # akapit, na podstronę
  order: int                                # 0–11, kolejność/limit 12

CharacterRelation (FK → Book, from_character FK, to_character FK)
  label: str                                # np. "matka", "wróg", "mentor" — skierowana
```

Monogram (inicjały + kolor) liczony na froncie z `name` — nie trzymany w bazie.

### Przepływ async

```
POST /generate
  └─ jeśli status pending/running → nic nie rób, zwróć istniejący status (idempotencja)
  └─ inaczej: CharacterAnalysis.status = pending, enqueue task(book_id), zwróć 202 + {status}

worker (concurrency 2–4)
  └─ status = running
  └─ klient OpenRouter (1 call, structured JSON)
       ├─ ok:    transaction → skasuj stare Character+Relation, zapisz nowe, status = done
       └─ błąd:  status = failed + error_message (parse/validation/brak klucza/HTTP)

frontend
  └─ po kliknięciu polling GET /characters/ co ~3 s aż status ∈ {done, failed}
```

„100 klików w tę samą książkę" = 1 job (idempotencja po statusie). Do OpenRoutera max 2–4 naraz.

## API (`characters/`)

| Endpoint | Auth | Rola |
|---|---|---|
| `POST /api/books/{slug}/characters/generate/` | zalogowany | enqueue job, `202` + `{status}` (idempotentne) |
| `GET /api/books/{slug}/characters/` | publiczny | `{status, characters: [...]}` — render sekcji + polling |
| `GET /api/books/{slug}/characters/{char_slug}/` | publiczny | postać + relacje (podstrona + ego-graf) |

Odczyt publiczny (jak szczegóły książki), generowanie tylko dla zalogowanych.

Serializery:
- `CharacterListSerializer` — `name, slug, role` (monogram liczony na froncie)
- `CharacterDetailSerializer` — `+ description, relations: [{to_slug, to_name, label}]`
- `CharacterAnalysisSerializer` — `status, error_message`

## Klient AI (`characters/ai.py`)

- Goły HTTP do OpenRouter chat completions, `response_format` = JSON. Stdlib `urllib` (spójnie z
  `import_books`, zero nowej zależności na sam call; Celery/Redis to osobne deps).
- Env: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` (settings dev/prod split).
- Prompt: „Dla książki «{title}» ({authors}) podaj do 12 najistotniejszych postaci. Dla każdej:
  name, role, description (1 akapit). Oraz relacje między nimi: from, to, label. Zwróć ścisły JSON
  wg schematu." Walidacja serializerem → parse/validation fail = `status=failed`.
- Brak `OPENROUTER_API_KEY` → task kończy `failed` z czytelnym `error_message` (nie wywala workera).

## Frontend

- **Sekcja na `/books/[slug]`** — `CharacterSection.svelte` pod opisem, nad recenzjami:
  - brak analizy → przycisk **„Generate AI"** po prawej (tylko zalogowany)
  - `pending/running` → „Generating…" + spinner, polling co ~3 s
  - `done` → siatka `CharacterCard.svelte` (monogram, klikalna)
  - `failed` → komunikat + „Try again"
- **Podstrona** `/books/[slug]/characters/[charSlug]/` — info o postaci + `RelationGraph.svelte`
  (ręczny ego-SVG, węzły to `<a href>` na inne postacie tej książki).
- Util `monogram(name)` → inicjały + kolor z hash imienia (deterministyczny, zero deps).

## Infra

- **+1 kontener `redis`** (broker + result backend) w `infra/compose` (dev; prod później).
- **+1 serwis `celery`** — ten sam obraz `django`, komenda `celery -A config worker`.
- `make dev-up` startuje: db, redis, django, celery, svelte.
- Konfiguracja Celery w `config/` (app, autodiscover tasks, `CELERY_TASK_ALWAYS_EAGER` w testach).

## Testy

- **Backend**: mock `urlopen` (jak `import_books`) — happy path, niepoprawny JSON → failed,
  idempotencja enqueue, gating (anonim nie wygeneruje), publiczny odczyt. Celery w testach
  `CELERY_TASK_ALWAYS_EAGER=True`.
- **OpenAPI**: regeneracja snapshotu (`make regenerate-openapi`).
- **E2E**: 1 scenariusz z zastubowaną generacją lub pominięty (LLM w E2E kruchy — decyzja w planie).

## Dokumentacja

- **ADR-003** — wprowadzenie Celery + Redis + zewnętrznego providera LLM (uzasadnienie odrzucenia sync).
- Update `ARCHITECTURE.md` (nowa app, kontenery, API surface) i `ROADMAP.md` (M13).

## Poza zakresem (YAGNI)

- Rate-limiting / throttle generacji (odłożone — znane ryzyko).
- Generacja z pełnego tekstu książki (nie mamy treści; LLM z własnej wiedzy).
- Zdjęcia/awatary postaci (brak źródła grafik).
- Pełny graf obsady (force-directed) — tylko ego-graf.
- Edycja/korekta postaci przez usera.
- Powiadomienia o zakończeniu generacji (poza pollingiem).
