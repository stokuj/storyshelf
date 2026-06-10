# API Contract

Snapshot OpenAPI 3.x dla backendu StoryShelf — wykonywalny kontrakt API.

## Pliki

- `openapi.yml` — wygenerowany schemat (drf-spectacular). Snapshotowany do repo, weryfikowany testem `config.tests.test_openapi_schema`.

## Regeneracja

Po kazdej zmianie API (nowy endpoint, zmiana serializera, nowe pole):

    make regenerate-openapi

Zacommittuj zmieniony `docs/api/openapi.yml` w tym samym PR-ze co zmiana backendu. Jezeli zapomnisz — CI faila na `config.tests.test_openapi_schema.OpenAPISchemaSnapshotTest`.

## Konsumpcja

Plik służy wyłącznie jako snapshot kontraktu pilnowany testem `config/tests/test_openapi_schema.py`. Generacja typów TS (`openapi-typescript`) — niezaimplementowana; ewentualnie „Kiedyś" (patrz ROADMAP).
