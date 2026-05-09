# Spec: storyshelf Monorepo

**Date:** 2026-05-09
**Repo:** github.com/stokuj/storyshelf

## Cel

Polaczenie dwoch osobnych repozytoriow (springshelf i storyweave) w jedno monorepo storyshelf z zachowaniem pelnej historii commitow (git subtree).

## Struktura katalogow

```
storyshelf/
├── backend/               ← Java Spring Boot (przeniesiony z springshelf/backend/)
├── frontend/              ← Vue 3 (przeniesiony z springshelf/frontend/)
├── nlp-service/           ← Python FastAPI (przeniesiony z storyweave/)
├── infra/
│   ├── compose/
│   │   ├── docker-compose.dev.yml     ← dev, bez Caddy, otwarte porty
│   │   └── docker-compose.prod.yml    ← prod, z Caddy (TLS)
│   ├── caddy/
│   │   └── Caddyfile
│   ├── scripts/
│   │   └── (deploy.sh itp.)
│   └── .env.example
├── Makefile
├── .github/workflows/     ← scalone CI z obu repo
├── .gitignore
└── README.md
```

## Metoda: git subtree

```bash
mkdir storyshelf && cd storyshelf && git init
git remote add origin https://github.com/stokuj/storyshelf.git
git subtree add --prefix=backend https://github.com/stokuj/springshelf.git main
git subtree add --prefix=nlp-service https://github.com/stokuj/storyweave.git main
```

Frontend nie jest osobnym repo — zostanie recznie przeniesiony (git mv) z `backend/frontend/` → `frontend/` po mergu.

## Makefile

```makefile
.PHONY: dev-up dev-down dev-status prod-up prod-down prod-status prod-logs

COMPOSE_DIR = infra/compose

dev-up:
    docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml up -d
dev-down:
    docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml down
dev-status:
    docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml ps

prod-up:
    docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml up -d
prod-down:
    docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml down
prod-status:
    docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml ps
prod-logs:
    docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml logs -f
```

## Kolejnosc implementacji

1. Stworzenie `storyshelf/` i `git subtree add` dla backend i nlp-service
2. Przeniesienie frontendu: `git mv backend/frontend frontend`
3. Stworzenie `infra/compose/` z ujednoliconymi docker-compose
4. Stworzenie `infra/caddy/Caddyfile`
5. Stworzenie `infra/scripts/` z skryptami
6. Stworzenie `Makefile` w root
7. Scalanie CI/CD (`.github/workflows/`)
8. Root `.gitignore`
9. Root `README.md`
10. Weryfikacja — `git log` sprawdza historie, buildy dzialaja
11. Push na github.com/stokuj/storyshelf
12. Archiwizacja starych repo na GitHub

## Ryzyka

- Frontend po `git subtree` jest w `backend/frontend/` — trzeba go przeniesc osobno (git mv)
- Docker compose'y springshelf odnosza sie do `springshelf/` → poprawic na `backend/`
- CI workflows maja zakodowane sciezki — trzeba zaktualizowac
- Commit hashe zmienione przez subtree — normalne
