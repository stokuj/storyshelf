# Infrastructure Hardening (Issue #33) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zredukować rozmiar obrazu NLP o ~200MB przez multi-stage build i zaktualizować ssh-action w CI.

**Architecture:** Dwie niezależne zmiany: (1) `nlp-service/Dockerfile` dostaje drugi stage budowy — `build-essential` tylko w stage build, finalny obraz ma tylko `curl` + `.venv` + kod; (2) `.github/workflows/ci.yml` — bump wersji akcji SSH.

**Tech Stack:** Docker, GitHub Actions, Python 3.13-slim, uv

---

### Task 1: Multi-stage NLP Dockerfile

**Files:**
- Modify: `nlp-service/Dockerfile` (cały plik)

- [ ] **Step 1: Zastąp Dockerfile wieloetapową wersją**

Zastąp całą zawartość `nlp-service/Dockerfile`:

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

- [ ] **Step 2: Zweryfikuj składnię Dockerfile**

```bash
docker build --dry-run -f nlp-service/Dockerfile nlp-service/ 2>&1 || true
```

Jeśli `--dry-run` nie jest wspierane, pomiń — walidacja nastąpi w CI.

- [ ] **Step 3: Commit**

```bash
git add nlp-service/Dockerfile
git commit -m "infra: multi-stage Dockerfile for nlp-service (issue #33)"
```

---

### Task 2: Bump appleboy/ssh-action in CI

**Files:**
- Modify: `.github/workflows/ci.yml:122`

- [ ] **Step 1: Zaktualizuj wersję akcji**

Zmień linię 122 w `.github/workflows/ci.yml`:

```diff
-        uses: appleboy/ssh-action@v1.0.3
+        uses: appleboy/ssh-action@v1.2.2
```

- [ ] **Step 2: Zweryfikuj składnię YAML (opcjonalne — lokalnie)**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "infra: bump appleboy/ssh-action to v1.2.2 (issue #33)"
```

---

### Task 3: Final verification

- [ ] **Step 1: Sprawdź stan repozytorium**

```bash
git status
git log --oneline -3
```

Oczekiwane: 2 nowe commity na branchu `infra/issue-33-hardening`, czysty working tree.
