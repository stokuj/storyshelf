# API Contract

Snapshot OpenAPI 3.x dla backendu StoryShelf — wykonywalny kontrakt API.

## Pliki

- `openapi.yml` — wygenerowany schemat (drf-spectacular). Snapshotowany do repo, weryfikowany testem `config.tests.test_openapi_schema`.

## Regeneracja

Po kazdej zmianie API (nowy endpoint, zmiana serializera, nowe pole):

    make regenerate-openapi

Zacommittuj zmieniony `docs/api/openapi.yml` w tym samym PR-ze co zmiana backendu. Jezeli zapomnisz — CI faila na `config.tests.test_openapi_schema.OpenAPISchemaSnapshotTest`.

## Konsumpcja (Phase 3.0+)

Frontend Svelte generuje typy TS z tego pliku przez `openapi-typescript` (do dodania w Phase 3.0). W Phase 2.0 plik istnieje tylko jako test kontraktu — bezposrednich konsumentow w runtime brak.
