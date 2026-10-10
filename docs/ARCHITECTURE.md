# Architecture — StoryShelf (wiki o książkach)

> Stan docelowy po pivocie 2026-10-03 ([ADR-004](decisions/ADR-004-wiki-okf-pages-in-postgres.md), [ADR-005](decisions/ADR-005-react-vite-spa.md)).
> Kod na `dev` po M1: szkielet backendu (`users`, `config`) i SPA na fake danych. Reszta (Strony, Agent, deploy SPA) w GitHub milestones.
> Słownik pojęć: [CONTEXT.md](../CONTEXT.md).

## Idea

Każdy User ma prywatną **Wiki** o przeczytanych książkach. Książki dodaje rozmową z **Agentem** (LLM). Agent pokazuje **Kandydata**, a po potwierdzeniu tworzy **Stronę** z pustego **Szablonu**. Następnie na żądanie ją **Generuje**, a późniejsze zmiany zgłasza jako **Propozycje**. Treść Stron jest zgodna z **OKF v0.2** (Markdown + frontmatter YAML).

## Tech Stack

| Warstwa   | Technologia |
|-----------|-------------|
| Frontend  | React 19 + Vite SPA (bez SSR) + TypeScript + TanStack Router/Query + Tailwind v4 + shadcn/ui + react-markdown |
| Backend   | Django 6 + DRF + Python 3.13 |
| Agent     | Celery + Redis, OpenRouter (ADR-003); czat przez SSE |
| Auth      | JWT: access i refresh w HttpOnly cookies (ADR-001) |
| Baza      | PostgreSQL 16 (później + pgvector) |
| Infra     | Docker Compose, Caddy (proxy `/api`; serwowanie statycznego buildu SPA jeszcze nie skonfigurowane) |

## Kontenery

```
caddy ──┬── statyczny build React (prod)
        └── /api → django (:8000) → db (PostgreSQL)
                         ↕
                 redis ← celery worker (Agent)
```

W dev frontend to `vite dev` z proxy `/api` → django (same-origin, ADR-002).

## Model danych (docelowy)

```
User
 ├── Profile (about, is_public)
 │    └── Favorite → Page (type book|character)
 └── Page (wiki_owner=User, path, type — unikalne (owner, path))
      ├── content: aktualny surowy .md (frontmatter + treść)
      ├── PageVersion (content, kind: created|generation|proposal|edit, author: human|agent, created_at)   ← Historia
      └── Proposal (proposed content, prompt, base_version → PageVersion, status: open|accepted|rejected|stale)
AgentConversation / message — czat dodawania książki (Kandydaci)
```

Pola z frontmattera potrzebne do zapytań (`type`, `title`, `book`, `universe`) są denormalizowane do kolumn przy zapisie. Źródłem prawdy pozostaje `content`.

Aktualna Wersja Strony to jej najnowszy `PageVersion` (bez osobnego wskaźnika). API zwraca jej id jako `version`, a Edycja odsyła je jako `base_version`; nieaktualne → 409.

Profil (`about`, `is_public`) to na razie pola `User.bio` i `User.profile_public` — bez osobnego modelu, dopóki nie dojdą Ulubione (#86).

Usunięte w M1: Book, Author, Genre, Tag, Serie, Rating, Review, ReviewLike, Shelf, ShelfMembership, ShelfEntry, UserFollow, feed, CharacterAnalysis, Character, CharacterRelation.

## Ścieżki (płaskie per typ)

```
/universes/wiedzmin.md
/books/ostatnie-zyczenie.md                    universe: /universes/wiedzmin.md (opcjonalne)
/characters/geralt--ostatnie-zyczenie.md       book: /books/ostatnie-zyczenie.md
/places/kaer-morhen--krew-elfow.md             book: /books/krew-elfow.md
```

Postacie i Miejsca są na razie per książka. Później zostaną scalone do Uniwersum (`/characters/geralt.md`).

## Przepływy

1. **Dodanie książki:** czat → Agent zwraca Kandydatów (tytuł, autor, rok, okładka) → User potwierdza → Strona z pustym Szablonem (`status: draft`).
2. **Generowanie:** przycisk na pustej Stronie → task Celery → treść + Wzmianki + Strony Postaci/Miejsc → Wersja (bez akceptacji).
3. **Propozycja:** User prosi Agenta na Stronie → Proposal z diffem, powiązany z bieżącą Wersją (`base_version`) → akceptacja tworzy Wersję i dopisuje zdarzenie `verified: [{by: human:<id>, at: <ISO8601>}]` (OKF v0.2 §5.2), odrzucenie niczego nie zmienia. Jeśli Strona dostała w międzyczasie nową Wersję (np. Edycję), Propozycja jest `stale`: akceptacja jest zablokowana, a jedyna akcja to ponowne wygenerowanie na bieżącej Wersji.
4. **Edycja:** textarea Markdown → nowa Wersja od razu (walidacja nagłówków Szablonu).
5. **Eksport:** cała Wiki jako pakiet OKF (`.tar` z plikami `.md` + `index.md` z `okf_version`).

## API (docelowe, szkic)

```
/api/auth/                         register, login, refresh, logout
/api/users/me/                     konto, settings
/api/u/{handle}/                   publiczny Profil (o mnie + karty Ulubionych, bez linków)
/api/wiki/pages/?type=             lista Stron (panel boczny)
/api/wiki/pages/{path}             odczyt / Edycja Strony
/api/wiki/pages/{path}/versions/   Historia
/api/wiki/pages/{path}/generate/   Generowanie (202, async)
/api/wiki/pages/{path}/proposals/  Propozycje (utwórz / akceptuj / odrzuć)
/api/agent/chat/                   czat z Agentem (SSE), Kandydaci
/api/wiki/export/                  pakiet OKF
```

## Testy

- Backend: `DJANGO_ENV=dev uv run python manage.py test`; walidacja OKF (frontmatter, `type`) jako unit testy.
- Agent: `CELERY_TASK_ALWAYS_EAGER=True` + mock OpenRoutera.
- Frontend: `tsc`, ESLint, Vitest; E2E Playwright.
