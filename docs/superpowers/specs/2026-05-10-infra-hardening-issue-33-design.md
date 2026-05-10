# Design: Infrastructure Hardening (Issue #33)

## Overview

Zbiorczy issue dla 2 ostrzeżeń infrastrukturalnych:
1. Multi-stage build dla `nlp-service/Dockerfile` — usunięcie `build-essential` z finalnego obrazu
2. Bump `appleboy/ssh-action` w CI workflow

## 1. NLP Dockerfile — Multi-stage Build

### Problem

Obecny `nlp-service/Dockerfile` używa pojedynczego `FROM python:3.13-slim`. W linii 8 instalowane jest `build-essential` (gcc, g++, make, ~200MB), które pozostaje w finalnym obrazie — niepotrzebne do działania serwisu w produkcji.

### Rozwiązanie

Dwa stage:

**Stage 1 (`build`):**
- `FROM python:3.13-slim AS build`
- Instaluje `build-essential`, `curl`, `uv`
- Wykonuje `uv sync --frozen --no-dev`
- Produkuje `.venv` ze wszystkimi zależnościami

**Stage 2 (finalny):**
- `FROM python:3.13-slim`
- Instaluje tylko `curl` (do healthchecka)
- Kopiuje `.venv`, kod (`api/`), `pyproject.toml`, `uv.lock`, `README.md` z build stage'a
- EXPOSE 8000, HEALTHCHECK, CMD bez zmian

### Nowy Dockerfile

```dockerfile
FROM python:3.13-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api ./api
RUN uv sync --frozen --no-dev


FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/api /app/api
COPY --from=build /app/pyproject.toml /app/pyproject.toml
COPY --from=build /app/uv.lock /app/uv.lock
COPY --from=build /app/README.md /app/README.md

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health/ || exit 1

CMD ["uv", "run", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Uzasadnienie decyzji

- **`curl` w finalnym stage**: Zachowuje istniejący healthcheck bez zmian. Koszt ~1-2MB.
- **Bez `uv` w finalnym stage**: `uv` jest już wewnątrz `.venv` jako zależność — `uv run` działa poprawnie.
- **`pyproject.toml`/`uv.lock` kopiowane**: Wymagane przez `uv run` do poprawnego działania.

### Oszczędność

~200MB na rozmiarze finalnego obrazu (usunięcie `build-essential`: gcc, g++, make i zależności).

## 2. CI Workflow — Bump ssh-action

### Problem

`.github/workflows/ci.yml:122` używa `appleboy/ssh-action@v1.0.3`. Najnowsza wersja to `v1.2.2` — 1.5 roku poprawek bezpieczeństwa i bugfixów.

### Rozwiązanie

Zmiana jednej linii:
```diff
-        uses: appleboy/ssh-action@v1.0.3
+        uses: appleboy/ssh-action@v1.2.2
```

### Ryzyko

Minimalne — zmiana w ramach tej samej major version (v1). API akcji nie zmieniło się w sposób breaking.

## Pliki zmieniane

| Plik | Zmiana |
|------|--------|
| `nlp-service/Dockerfile` | Multi-stage build (przepisanie całego pliku) |
| `.github/workflows/ci.yml` | `v1.0.3` → `v1.2.2` (1 linia) |

## Weryfikacja

- Budowa obrazu NLP: `docker build -t storyshelf-nlp nlp-service/`
- CI workflow: review składni YAML, CI przechodzi na PR
