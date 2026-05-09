# Spec: Pełny Audyt Monorepo storyshelf

**Date:** 2026-05-09
**Branch:** audit/full-project-review

## Cel

Przeprowadzenie pełnego audytu wszystkich modułów monorepo storyshelf: backend (Spring Boot), frontend (Vue 3), nlp-service (Python FastAPI), infrastruktura, integracja Spring-FastAPI, oraz luki ogólne. Wykonany jako 6 niezależnych subagentów.

## Moduły audytu

### Moduł 1: Backend (Spring Boot)

- Struktura kontrolerów — endpointy, HTTP methods, statusy
- Serwisy — logika biznesowa
- Repozytoria — zapytania JPA
- Kafka — AnalysisResultConsumer, ChapterEventProducer
- DTO — NerResult, PairResult, AnalyseResponse vs FastAPI
- Exception handler — GlobalExceptionHandler
- Security — SecurityConfig, JWT, RoleConfig
- Testy — mvn test, coverage
- Dead code — nieużywane klasy/metody
- application.yml — profile dev/prod

### Moduł 2: Frontend (Vue 3)

- Router — ścieżki + komponenty
- API klient (api.js) — endpointy vs backend
- Auth flow (auth.js) — login, token
- Komponenty widoków — loading/empty/error/data states
- Zgodność z backendem — vite proxy

### Moduł 3: nlp-service (Python FastAPI)

- Serwisy — llm_engine, transformers_engine, text_parser, text_stats
- Workflowy — analyse, find_pairs, ner, relations
- Celery — taski, kolejki
- Kafka — consumer, producer — topic names
- Endpointy — parametry, działanie
- Config — settings.py, celery_app.py
- Testy — uv run pytest, coverage
- Dead code — refactor.py
- Dockerfile — warstwy optymalizacja

### Moduł 4: Infrastruktura

- docker-compose.dev.yml — context paths, porty, zależności
- docker-compose.prod.yml — image names, Caddy routing
- Caddyfile — reverse proxy
- CI/CD — actions syntax, wersje
- Makefile — targety
- Dockerfile'e — optymalizacja
- .gitignore — kompletność

### Moduł 5: Integracja Spring ↔ FastAPI

- Mapa Kafka topiców — producer/consumer
- Kontrakty JSON — DTO vs modele
- Przepływ NER — książka → chapter → Kafka → NER → DB
- Przepływ Relations — relacje między postaciami
- Error handling — FastAPI down, Kafka down
- Idempotencja

### Moduł 6: Luki ogólne

- Security — env z kluczami, CORS prod
- Dokumentacja — README, data_flow.md vs rzeczywistość
- Brakujące pliki — .env.example vs zmienne
- Nieużywane zależności — pom.xml, pyproject.toml, package.json
- Monitoring/logging
- Health checki

## Format wyników

Każdy moduł zwraca:

```
## Moduł X: [Nazwa]

### Bugs (do naprawy natychmiast)
- [BUG] opis • plik:linia • przyczyna

### Warnings (do naprawy wkrótce)
- [WARN] opis • plik:linia

### Suggestions (opcjonalne)
- [SUG] opis • plik:linia
```
