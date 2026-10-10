# Spec — API Stron wiki: walidacja OKF i Wersje (#108)

> Data: 2026-10-10 · Issue: #108 · Milestone: M2 · Decyzje: ADR-004 · Bazuje na: #88 (fixtures `.md`), #92 (`TEMPLATES`, `validateEdit`), #91 (`slugify`, `createBook`) · Model: `docs/ARCHITECTURE.md` · Spike: `docs/superpowers/specs/2026-10-03-spike-94-agent-okf-page.md` · Pojęcia: `CONTEXT.md` (Strona, Ścieżka, Szablon, Wersja, Edycja)

## Cel

Backend przechowuje Strony Wiki w Postgresie. Każdy zapis jest walidowany jako OKF (frontmatter, `type`, nagłówki Szablonu) i zostawia Wersję. Edycja na nieaktualnej Wersji dostaje 409 zamiast nadpisać Stronę. Seed wgrywa Wiedźmina i Solaris, więc #110 może podpiąć ekrany M1 pod prawdziwe API. Frontend się nie zmienia.

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Warstwy | `wiki/okf.py` (czyste funkcje) + `wiki/services.py` (transakcje, Wersje, 409) + cienkie widoki DRF | Agent w M3 (Celery) użyje tych samych serwisów co API; walidacja testowalna bez bazy |
| Aktualna Wersja | najnowszy `PageVersion` Strony (`-id`), bez osobnego wskaźnika; API zwraca jej id jako `version` | mniej stanu do synchronizacji |
| Ścieżka | liczy serwer: `/books/{slug}.md`, `/universes/{slug}.md`, `/characters/{slug}--{slug Ścieżki book}.md`, `/places/…` analogicznie | jedno miejsce dla slugify i Szablonów (UI + Agent M3) |
| `slugify` | port 1:1 z `frontend/src/wiki.ts`: `ł→l`, NFD bez znaków łączących, małe litery, nie-alfanumeryczne → `-`, przycięte | Ścieżki zgodne z istniejącymi fixtures |
| Niezmienność Ścieżki | Edycja może zmienić `title`, Ścieżka zostaje; zmiana `type` → 400 | Ścieżka = tożsamość (OKF) |
| `book` / `universe` przy tworzeniu | `character`/`place` wymaga `book` = istniejąca Strona `book` w tej samej Wiki; opcjonalne `universe` książki = istniejąca Strona `universe`; inaczej 400 | brak sierot przy tworzeniu; przy Edycji nie sprawdzamy (Odnośniki też mogą prowadzić donikąd) |
| Szablon | wymagane nagłówki `##` muszą być, dodatkowe sekcje dozwolone | jak `validateEdit` w M1 |
| Zapis treści | Edycja zapisuje `content` bajt w bajt; `yaml.safe_dump` tylko przy składaniu pustego Szablonu | issue: bez re-dumpowania frontmattera |
| Komunikaty błędów | identyczne jak w `validateEdit` (`Missing template headings: …`, `Page type can't change`, `Invalid frontmatter: …`) | frontend pokaże je bez mapowania |
| Dostęp | `IsAuthenticated` na każdym widoku, queryset `owner=request.user`; cudza Strona → 404 | domyślne `IsAuthenticatedOrReadOnly` przepuściłoby GET |
| Lista Stron | bez paginacji, bez `content` | panel boczny potrzebuje całości |
| Lista Wersji | standardowa paginacja (`data/page/per_page/total`), z `content`, od najnowszej | Historia może urosnąć |
| Fixtures | kopia 15 plików `.md` w `backend-django/wiki/fixtures/`; kopia we frontendzie znika w #110 | kontener django nie widzi `frontend/`; bez zmian w Vite |
| Seed | `manage.py seed <email>`, istniejący User; jedna Wersja `created`/`human` na Stronę; istniejąca Ścieżka pomijana | idempotentny, nie tworzy kont ani haseł |
| PyYAML | jawnie w `pyproject.toml` | dziś przychodzi tranzytywnie |

## Pliki

```
backend-django/
  pyproject.toml                         + pyyaml
  config/settings/base.py                + "wiki" w INSTALLED_APPS
  config/urls.py                         + path("api/wiki/", include("wiki.urls"))
  wiki/
    __init__.py, apps.py, admin.py
    models.py                            Page, PageVersion
    migrations/0001_initial.py
    okf.py                               OKFError, TEMPLATES, parse, validate, slugify, page_path, render_template
    services.py                          PathTaken, StaleVersion, create_page, edit_page
    serializers.py                       PageListSerializer, PageSerializer, PageCreateSerializer, PageEditSerializer, PageVersionSerializer
    views.py                             PageListCreateView, PageDetailView, PageVersionListView
    urls.py
    management/commands/seed.py
    fixtures/{books,characters,places,universes}/*.md   (kopia z frontend/src/api/fixtures/)
    tests/test_okf.py, test_pages_api.py, test_seed.py
docs/api/openapi.yml                     regenerowany (make regenerate-openapi)
docs/ARCHITECTURE.md                     + linia: aktualna Wersja = najnowszy PageVersion
```

## Model

`Page`

| Pole | Typ | Uwagi |
|---|---|---|
| `owner` | FK → User, `CASCADE` | |
| `path` | `CharField` | `/books/solaris.md`; `UniqueConstraint(owner, path)` |
| `type` | `CharField` choices | `book`, `character`, `place`, `universe` |
| `title` | `CharField` | z frontmattera |
| `book`, `universe` | `CharField`, nullable | z frontmattera (Ścieżki) |
| `content` | `TextField` | surowy `.md`, źródło prawdy |
| `created_at`, `updated_at` | `DateTimeField` | auto |

`PageVersion`: `page` FK (`CASCADE`, `related_name="versions"`), `content`, `kind` (`created|generation|proposal|edit`), `author` (`human|agent`), `created_at`. `ordering = ["-id"]`.

## Interfejsy

### `wiki/okf.py`

```python
class OKFError(ValueError): ...           # message = komunikat dla Usera; .field = klucz błędu (domyślnie "content")

TEMPLATES: dict[str, list[str]]           # jak wiki.ts:64
def parse(content: str) -> tuple[dict, str]           # regex frontmattera z wiki.ts, yaml.safe_load
def validate(content: str, page_type: str) -> dict    # zwraca frontmatter albo rzuca OKFError
def slugify(text: str) -> str
def page_path(page_type: str, title: str, book: str | None = None) -> str   # pusty slug → OKFError(field="title")
def render_template(page_type: str, meta: dict) -> str   # frontmatter + status: draft + puste nagłówki
```

Kolejność sprawdzeń w `validate` (pierwszy błąd przerywa):

1. Frontmatter istnieje i jest poprawnym YAML → `Invalid frontmatter: …`
2. Frontmatter jest mapą → `Invalid frontmatter: not a mapping`
3. `type` obecny → `Missing type`; równy typowi Strony → `Page type can't change`
4. `title` to niepusty string → `Missing title`
5. Wszystkie nagłówki `TEMPLATES[type]` obecne jako linie `## …` (po `strip`) → `Missing template headings: A, B`

### `wiki/services.py`

```python
class PathTaken(Exception): ...
class StaleVersion(Exception): ...

def insert_page(owner, path, page_type, content) -> Page
def create_page(owner, page_type, title, *, author=None, year=None, book=None, universe=None) -> Page
def edit_page(page, content, base_version: int, *, kind="edit", author="human") -> Page
```

- `insert_page`: `validate`, potem w `transaction.atomic` zapisuje `Page` (z polami denormalizowanymi) i `PageVersion(kind="created", author="human")`. `IntegrityError` z constraintu `(owner, path)` → `PathTaken("Page already exists: <path>")`. Używają go `create_page` i seed.
- `create_page`: sprawdza `book`/`universe` (`OKFError` z `field="book"`/`"universe"`), liczy Ścieżkę, składa Szablon, woła `insert_page`.
- `edit_page`: w `transaction.atomic` blokuje Stronę (`select_for_update`); najnowsza Wersja ≠ `base_version` → `StaleVersion`, nic się nie zapisuje. Inaczej `validate`, aktualizacja `content` i pól denormalizowanych, nowa `PageVersion`. `kind`/`author` istnieją dla Agenta w M3; endpoint zawsze wysyła `edit`/`human`.

### HTTP

| Metoda i URL | Body | Sukces | Błędy |
|---|---|---|---|
| `GET /api/wiki/pages/?type=` | | `200` `[{path, type, title, book, universe}]` | `401` |
| `POST /api/wiki/pages/` | `{type, title, author?, year?, book?, universe?}` | `201` Strona | `400` per pole / `{"content": [msg]}`, `409` zajęta Ścieżka |
| `GET /api/wiki/pages/{path}` | | `200` `{path, type, title, book, universe, content, version}` | `404` |
| `PUT /api/wiki/pages/{path}` | `{content, base_version}` | `200` Strona z nowym `version` | `400 {"content": [msg]}`, `404`, `409` nieaktualna Wersja |
| `GET /api/wiki/pages/{path}/versions/` | | `200` paginowane `{id, kind, author, content, created_at}` od najnowszej | `404` |

`{path}` w URL to Ścieżka bez wiodącego `/`, dopasowana regexem `(?P<path>(books|characters|places|universes)/[a-z0-9-]+\.md)`. Widoki mapują `OKFError` → 400 `{<field>: [msg]}` (`content`, `title`, `book` albo `universe`), `PathTaken`/`StaleVersion` → 409 `{"detail": msg}`; `@extend_schema` opisuje 400 i 409 w OpenAPI.

### Seed

`manage.py seed <email>`: brak Usera → `CommandError`. Każdy plik: Ścieżka z położenia pliku (`/books/solaris.md`), `insert_page`; `PathTaken` → pominięta, `OKFError` → `CommandError` z Ścieżką. Wypisuje `created N, skipped M`. Seed nie sprawdza `book`/`universe` (to robi tylko `create_page`). Fixture, który nie przejdzie walidacji, poprawiamy w kopii backendowej.

## Testy

| Plik | Co sprawdza | Done when |
|---|---|---|
| `wiki/tests/test_okf.py` | każdy komunikat z `validate`; CRLF; dodatkowe sekcje OK; `slugify("Krew elfów") == "krew-elfow"`, `ł`; `page_path` dla 4 typów; `render_template` przechodzi `validate` | 1 |
| `wiki/tests/test_pages_api.py` | POST bez `type` / zły `type` → 400 per pole; PUT bez nagłówka / ze zmienionym `type` → 400 `content`; POST tworzy Wersję `created`; PUT dodaje Wersję, `versions/` od najnowszej; nieaktualna `base_version` → 409 i treść bez zmian; zajęta Ścieżka → 409; Postać bez istniejącej książki → 400; cudza Strona → 404 (GET, PUT, versions); bez logowania → 401; `?type=` filtruje | 1–4 |
| `wiki/tests/test_seed.py` | 15 Stron i 15 Wersji; drugi przebieg nic nie dodaje; nieznany email → `CommandError` | 5 |
| `config.tests.test_openapi_schema` | snapshot po `make regenerate-openapi` | 5 |

Bramka: `make verify` przechodzi.

## Poza zakresem

Zmiany we frontendzie (#110), Propozycje (M3), eksport (#113), Ulubione (#112), walidacja Odnośników, paginacja listy Stron, usuwanie Stron.
