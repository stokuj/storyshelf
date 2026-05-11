# storyshelf Monorepo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Merge two separate repos (springshelf + storyweave) into one `github.com/stokuj/storyshelf` monorepo with `backend/`, `frontend/`, `nlp-service/`, and `infra/` directories.

**Architecture:** `git subtree add` preserves commit history by prefixing all file paths with the target directory name. After subtree merge, manual `git mv` extracts `frontend/` from `backend/`. Docker compose, Caddy, and CI are unified under `infra/` and `.github/`.

**Tech Stack:** git subtree, Docker Compose, Caddy, GitHub Actions, Make

**Repo location:** `/home/dv6/GitHub/storyshelf` (already initialized with spec commit)

---

### Task 1: Merge springshelf as `backend/` via git subtree

**Files:**
- Creates: `backend/` (entire springshelf repo content)

- [ ] **Step 1: Add springshelf remote and fetch**

Run in `/home/dv6/GitHub/storyshelf`:
```bash
git remote add springshelf https://github.com/stokuj/springshelf.git
git fetch springshelf main
```
Expected: fetches all commits from springshelf, no errors.

- [ ] **Step 2: git subtree add backend**

```bash
git subtree add --prefix=backend springshelf main
```
Expected: creates `backend/` with all springshelf files. Output shows `Merge commit 'xxxx' as 'backend/'`.

- [ ] **Step 3: Verify the structure**

```bash
ls backend/
```
Expected: sees `pom.xml`, `frontend/`, `backend/`, `docs/`, `docker-compose.dev.yml`, `docker-compose.prod.yml`, `Caddyfile`, `.env.example`, `.gitignore`, `README.md`, `.github/`.

- [ ] **Step 4: Verify full history is preserved (commit count)**

```bash
echo "Commits in backend/: $(git log --oneline -- backend/ | wc -l)"
echo "Commits in original springshelf: $(git -C /home/dv6/GitHub/BookNLP/springshelf log --oneline | wc -l)"
```
Expected: both numbers match (± a few due to merge commits). This proves ALL history was transferred, not just recent commits.

- [ ] **Step 5: Commit (subtree already committed)**

```bash
git log --oneline -1
```
Expected: already has the merge commit from `git subtree add`. No manual commit needed.

---

### Task 2: Merge storyweave as `nlp-service/` via git subtree

**Files:**
- Creates: `nlp-service/` (entire storyweave repo content)

- [ ] **Step 1: Add storyweave remote and fetch**

```bash
git remote add storyweave https://github.com/stokuj/storyweave.git
git fetch storyweave main
```
Expected: fetches all commits from storyweave, no errors.

- [ ] **Step 2: git subtree add nlp-service**

```bash
git subtree add --prefix=nlp-service storyweave main
```
Expected: creates `nlp-service/` with all storyweave files. Output shows `Merge commit 'xxxx' as 'nlp-service/'`.

- [ ] **Step 3: Verify the structure**

```bash
ls nlp-service/
```
Expected: sees `pyproject.toml`, `api/`, `test/`, `docs/`, `Dockerfile`, `docker-compose.dev.yml`, `.env.example`, `.gitignore`, `README.md`, `.github/`, `uv.lock`.

- [ ] **Step 4: Verify full history is preserved (commit count)**

```bash
echo "Commits in nlp-service/: $(git log --oneline -- nlp-service/ | wc -l)"
echo "Commits in original storyweave: $(git -C /home/dv6/GitHub/BookNLP/storyweave log --oneline | wc -l)"
```
Expected: both numbers match (± a few due to merge commits). This proves ALL history was transferred, not just recent commits.

---

### Task 3: Move frontend out of backend/

**Files:**
- Move: `backend/frontend/` → `frontend/`
- Stale: backend/frontend `.gitignore` remains at old location (will be removed by mv)

- [ ] **Step 1: git mv frontend to root level**

```bash
git mv backend/frontend frontend
```
Expected: moves entire `frontend/` directory to root. No errors.

- [ ] **Step 2: Verify new location**

```bash
ls frontend/
```
Expected: sees `package.json`, `src/`, `vite.config.js`, `Dockerfile`, `Dockerfile.prod`, `index.html`, `nginx.conf`, `tailwind.config.js`, `postcss.config.js`.

- [ ] **Step 3: Verify frontend is gone from backend/**

```bash
ls backend/frontend/ 2>&1
```
Expected: `No such file or directory`.

- [ ] **Step 4: Commit the move**

```bash
git commit -m "Move frontend from backend/ to root level"
```

---

### Task 4: Create infra/compose/ with unified docker-compose files

**Files:**
- Create: `infra/compose/docker-compose.dev.yml`
- Create: `infra/compose/docker-compose.prod.yml`

- [ ] **Step 1: Create infra directory structure**

```bash
mkdir -p infra/compose infra/caddy infra/scripts
```

- [ ] **Step 2: Create dev compose (unified, no Caddy)**

Write `infra/compose/docker-compose.dev.yml`:

```yaml
# Development environment — no Caddy, open ports for local dev
services:
  frontend:
    build:
      context: ../../frontend
      dockerfile: Dockerfile
    image: storyshelf-frontend:local
    container_name: frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_PROXY_TARGET: http://backend:8080
    restart: unless-stopped
    depends_on:
      backend:
        condition: service_started

  backend:
    build:
      context: ../../backend/backend
      dockerfile: Dockerfile
    pull_policy: build
    image: storyshelf-backend:local
    container_name: backend
    ports:
      - "8080:8080"
    env_file:
      - ../../.env
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-booksdb}
      SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER:-postgres}
      SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-secret-key}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      kafka:
        condition: service_started

  nlp-service:
    build:
      context: ../../nlp-service
      dockerfile: Dockerfile
    pull_policy: build
    image: storyshelf-nlp:local
    container_name: storyweave-api
    ports:
      - "8000:8000"
    env_file:
      - ../../.env
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      HF_HOME: /cache/huggingface
      TRANSFORMERS_CACHE: /cache/huggingface
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      SPRINGSHELF_BASE_URL: http://backend:8080
    volumes:
      - hf-cache:/cache/huggingface
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_started
      kafka:
        condition: service_started

  celery-worker:
    build:
      context: ../../nlp-service
      dockerfile: Dockerfile
    pull_policy: build
    image: storyshelf-nlp:local
    container_name: storyweave-celery-worker
    command: ["uv", "run", "celery", "-A", "api.config.celery_app:celery", "worker", "--loglevel=info"]
    env_file:
      - ../../.env
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      HF_HOME: /cache/huggingface
      TRANSFORMERS_CACHE: /cache/huggingface
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      SPRINGSHELF_BASE_URL: http://backend:8080
    volumes:
      - hf-cache:/cache/huggingface
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_started
      kafka:
        condition: service_started

  db:
    image: postgres:16
    container_name: books-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-booksdb}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret-key}
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-booksdb}"]
      interval: 5s
      timeout: 3s
      retries: 20
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: storyweave-redis
    volumes:
      - redis-data:/data
    restart: unless-stopped

  kafka:
    image: apache/kafka:3.7.0
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      - KAFKA_NODE_ID=1
      - KAFKA_PROCESS_ROLES=broker,controller
      - KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
    volumes:
      - kafka-data:/var/lib/kafka/data
    restart: unless-stopped

  redpanda-console:
    image: docker.redpanda.com/redpandadata/console:latest
    container_name: redpanda-console
    ports:
      - "8081:8080"
    environment:
      KAFKA_BROKERS: kafka:9092
    restart: unless-stopped
    depends_on:
      kafka:
        condition: service_started

volumes:
  db-data:
  redis-data:
  hf-cache:
  kafka-data:
```

- [ ] **Step 3: Create prod compose (unified, with Caddy)**

Write `infra/compose/docker-compose.prod.yml`:

```yaml
services:
  frontend:
    image: ghcr.io/stokuj/storyshelf-frontend:main
    container_name: frontend
    expose:
      - "80"
    restart: unless-stopped
    depends_on:
      - backend

  backend:
    image: ghcr.io/stokuj/storyshelf-backend:main
    container_name: backend
    expose:
      - "8080"
    env_file:
      - ../../.env
    environment:
      SPRING_DATASOURCE_URL: jdbc:postgresql://db:5432/${POSTGRES_DB:-booksdb}
      SPRING_DATASOURCE_USERNAME: ${POSTGRES_USER:-postgres}
      SPRING_DATASOURCE_PASSWORD: ${POSTGRES_PASSWORD:-secret-key}
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      kafka:
        condition: service_started

  nlp-service:
    image: ghcr.io/stokuj/storyshelf-nlp:main
    container_name: storyweave-api
    expose:
      - "8000"
    env_file:
      - ../../.env
    environment:
      APP_ENV: production
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      HF_HOME: /cache/huggingface
      TRANSFORMERS_CACHE: /cache/huggingface
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      SPRINGSHELF_BASE_URL: http://backend:8080
    volumes:
      - hf-cache:/cache/huggingface
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_started
      kafka:
        condition: service_started

  celery-worker:
    image: ghcr.io/stokuj/storyshelf-nlp:main
    container_name: storyweave-celery-worker
    command: ["uv", "run", "celery", "-A", "api.config.celery_app:celery", "worker", "--loglevel=info", "--concurrency=8"]
    env_file:
      - ../../.env
    environment:
      APP_ENV: production
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/0
      HF_HOME: /cache/huggingface
      TRANSFORMERS_CACHE: /cache/huggingface
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      SPRINGSHELF_BASE_URL: http://backend:8080
    volumes:
      - hf-cache:/cache/huggingface
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_started
      kafka:
        condition: service_started

  caddy:
    image: caddy:2-alpine
    container_name: storyshelf-caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ../caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    restart: unless-stopped
    depends_on:
      - frontend
      - backend
      - nlp-service

  db:
    image: postgres:16
    container_name: books-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-booksdb}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret-key}
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-booksdb}"]
      interval: 5s
      timeout: 3s
      retries: 20
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: storyweave-redis
    volumes:
      - redis-data:/data
    restart: unless-stopped

  kafka:
    image: apache/kafka:3.7.0
    container_name: kafka
    ports:
      - "9092:9092"
    environment:
      - KAFKA_NODE_ID=1
      - KAFKA_PROCESS_ROLES=broker,controller
      - KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER
      - KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
      - KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
    volumes:
      - kafka-data:/var/lib/kafka/data
    restart: unless-stopped

volumes:
  db-data:
  redis-data:
  hf-cache:
  caddy-data:
  caddy-config:
  kafka-data:
```

- [ ] **Step 4: Validate both compose files**

```bash
docker compose -f infra/compose/docker-compose.dev.yml config -q
docker compose -f infra/compose/docker-compose.prod.yml config -q
```
Expected: both commands silent (no errors). Note: `context` paths use `../../` because compose runs from project root and looks for context relative to compose file location.

- [ ] **Step 5: Commit**

```bash
git add infra/compose/docker-compose.dev.yml infra/compose/docker-compose.prod.yml
git commit -m "Add unified dev and prod docker compose files"
```

---

### Task 5: Create infra/caddy/Caddyfile

**Files:**
- Create: `infra/caddy/Caddyfile`

- [ ] **Step 1: Write Caddyfile**

Write `infra/caddy/Caddyfile` — same as original from springshelf with container name update:

```
:80 {
    handle /api/docs {
        rewrite * /docs
        reverse_proxy storyweave-api:8000
    }

    handle /api/docs/* {
        uri strip_prefix /api
        reverse_proxy storyweave-api:8000
    }

    handle /openapi.json* {
        reverse_proxy storyweave-api:8000
    }

    handle_path /v3/api-docs* {
        reverse_proxy backend:8080
    }

    handle_path /swagger-ui/* {
        reverse_proxy backend:8080
    }

    handle /docs {
        rewrite * /swagger-ui/index.html
        reverse_proxy backend:8080
    }

    handle_path /api/* {
        reverse_proxy backend:8080
    }

    handle_path /storyweave/* {
        reverse_proxy storyweave-api:8000
    }

    handle {
        reverse_proxy frontend:80
    }

    encode gzip
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy no-referrer
    }
    log {
        output stdout
    }
}
```

> Note: container names in Caddyfile match service container names in prod compose (`backend`, `frontend`, `storyweave-api`).

- [ ] **Step 2: Commit**

```bash
git add infra/caddy/Caddyfile
git commit -m "Add Caddy reverse-proxy config for prod"
```

---

### Task 6: Create infra/.env.example

**Files:**
- Create: `infra/.env.example`

- [ ] **Step 1: Write unified .env.example**

Write `infra/.env.example`:

```
### DATABASE
POSTGRES_DB=booksdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secret-key

### JAVA BACKEND
JWT_SECRET=replace-this-dev-secret-with-minimum-32-characters
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
DOMAIN=localhost
SPRING_PROFILES_ACTIVE=dev

### NLP SERVICE (Python/FastAPI)
OPENROUTER_API_KEY="sk-dummy-api-key"
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=qwen/qwen3.5-35b-a3b
LLM_MAX_TOKENS=1000
NER_MODEL=dbmdz/bert-large-cased-finetuned-conll03-english

### CORS
CORS_ALLOW_ORIGINS=https://your-domain.com
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*

APP_ENV=development
```

- [ ] **Step 2: Commit**

```bash
git add infra/.env.example
git commit -m "Add unified .env.example for whole monorepo"
```

---

### Task 7: Create infra/scripts/deploy.sh

**Files:**
- Create: `infra/scripts/deploy.sh`

- [ ] **Step 1: Write deploy script**

Write `infra/scripts/deploy.sh`:

```bash
#!/bin/bash
# Deploy script for storyshelf production
# Usage: ./deploy.sh [service...]
#   ./deploy.sh              → deploy all
#   ./deploy.sh backend nlp   → deploy specific services

set -e

COMPOSE_FILE="infra/compose/docker-compose.prod.yml"
SERVICES="${@:-}"

if [ -z "$SERVICES" ]; then
    echo "Pulling all images..."
    docker compose -f "$COMPOSE_FILE" pull
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate
else
    echo "Deploying services: $SERVICES"
    docker compose -f "$COMPOSE_FILE" pull $SERVICES
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate $SERVICES
fi

echo "---"
docker compose -f "$COMPOSE_FILE" ps
```

- [ ] **Step 2: Make executable**

```bash
chmod +x infra/scripts/deploy.sh
```

- [ ] **Step 3: Commit**

```bash
git add infra/scripts/deploy.sh
git commit -m "Add production deploy script"
```

---

### Task 8: Create root Makefile

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Write Makefile**

Write `Makefile`:

```makefile
.PHONY: dev-up dev-down dev-status dev-build prod-up prod-down prod-status prod-logs

COMPOSE_DIR = infra/compose

dev-up:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml up -d

dev-down:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml down

dev-status:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml ps

dev-build:
	docker compose -f $(COMPOSE_DIR)/docker-compose.dev.yml build

prod-up:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml up -d

prod-down:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml down

prod-status:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml ps

prod-logs:
	docker compose -f $(COMPOSE_DIR)/docker-compose.prod.yml logs -f
```

- [ ] **Step 2: Verify Makefile syntax**

```bash
make -n dev-up
```
Expected: prints the docker compose command without executing it.

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "Add root Makefile with dev and prod targets"
```

---

### Task 9: Create unified CI/CD (.github/workflows/ci.yml)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write unified CI workflow**

Write `.github/workflows/ci.yml`:

```yaml
name: Test & Build and Push Docker Images

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  NAMESPACE: stokuj

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "21"
          cache: maven

      - name: Run backend tests
        working-directory: backend/backend
        run: mvn -B test

  test-nlp:
    runs-on: ubuntu-latest
    env:
      OPENROUTER_API_KEY: fake-key
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        working-directory: nlp-service
        run: uv sync --frozen

      - name: Run tests
        working-directory: nlp-service
        run: uv run pytest -v -m "not integration"

      - name: Run coverage
        working-directory: nlp-service
        run: |
          uv run coverage run -m pytest -m "not integration"
          uv run coverage report --fail-under=70 --include="api/*"

  build-and-push:
    needs: [test-backend, test-nlp]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        include:
          - name: backend
            context: ./backend/backend
            dockerfile: ./backend/backend/Dockerfile
            image: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/storyshelf-backend
          - name: frontend
            context: ./frontend
            dockerfile: ./frontend/Dockerfile.prod
            image: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/storyshelf-frontend
          - name: nlp-service
            context: ./nlp-service
            dockerfile: ./nlp-service/Dockerfile
            image: ${{ env.REGISTRY }}/${{ env.NAMESPACE }}/storyshelf-nlp
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ matrix.image }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push ${{ matrix.name }}
        uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.context }}
          file: ${{ matrix.dockerfile }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy over SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.GCP_HOST }}
          username: ${{ secrets.GCP_USER }}
          key: ${{ secrets.GCP_SSH_KEY }}
          port: 22
          script: |
            cd /opt/storyshelf
            bash infra/scripts/deploy.sh
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "Add unified CI/CD pipeline for monorepo"
```

---

### Task 10: Create root .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Write root .gitignore**

Write `.gitignore`:

```
# Compiled class file
*.class

# Log file
*.log

# BlueJ files
*.ctxt

# Mobile Tools for Java (J2ME)
.mtj.tmp/

# Package Files #
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar

# virtual machine crash logs
hs_err_pid*
replay_pid*

# Environment
.env
backend/src/main/resources/application-local.properties
target/
backend/backend/target/
frontend/node_modules/

# IDE files
.idea/
*.iml
.vscode/
.ruff_cache/
# Allow .vscode/ from subdirectories that may need custom settings

# Frontend build artifacts
frontend/dist/

# Python
__pycache__/
*.py[codz]
*$py.class
*.so
*.egg-info/
.venv/
env/
venv/
.pytest_cache/
.coverage
htmlcov/

# Docker
caddy-data/
caddy-config/

# Celery
celerybeat-schedule
celerybeat.pid
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "Add root .gitignore for monorepo"
```

---

### Task 11: Create root README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README.md**

Write `README.md`:

```markdown
# storyshelf

A full-stack book tracking and literary analysis platform.

- **backend/** — Java Spring Boot REST API (book catalog, users, bookshelf, reviews, series)
- **frontend/** — Vue 3 SPA with Tailwind/daisyUI
- **nlp-service/** — Python FastAPI microservice for NER, character extraction, and LLM-based relation analysis
- **infra/** — Docker Compose, Caddy config, deploy scripts, shared .env.example

## Quick Start (Dev)

```bash
cp infra/.env.example .env
# edit .env with your keys
make dev-up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8080
- NLP Service: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8080/docs
- Kafka Console: http://localhost:8081

## Production

```bash
cp infra/.env.example .env
# edit .env with production values
make prod-up
make prod-logs
```

## Architecture

```
Browser → Caddy (reverse proxy) → Frontend (Vue 3 SPA)
                                → Backend (Spring Boot + PostgreSQL)
                                → NLP Service (FastAPI + Celery + Redis + Kafka)
```

Frontend talks to Backend via REST. Backend communicates with NLP Service asynchronously via Kafka for book analysis (NER, character extraction, relation extraction).

## Documentation

- [API Endpoints](docs/backend/api_endpoints.md)
- [Database Schema](docs/backend/database.md)
- [NLP Data Flow](docs/backend/data_flow.md)
- [User Stories](docs/backend/user_stories.md)
- [NLP Testing Guide](docs/nlp-service/request_examples.md)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Add root README for storyshelf monorepo"
```

---

### Task 12: Remove stale docker-compose and CI from subdirectories

**Files:**
- Remove: `backend/docker-compose.dev.yml`, `backend/docker-compose.prod.yml`, `backend/docker-compose.dev.build.yml`, `backend/docker-compose.dev.pull.yml`
- Remove: `backend/Caddyfile`
- Remove: `backend/.env.example`
- Remove: `backend/.github/`
- Remove: `nlp-service/docker-compose.dev.yml`
- Remove: `nlp-service/.github/`

- [ ] **Step 1: Remove stale files from backend/**

```bash
git rm backend/docker-compose.dev.yml backend/docker-compose.prod.yml backend/docker-compose.dev.build.yml backend/docker-compose.dev.pull.yml 2>/dev/null
git rm backend/Caddyfile 2>/dev/null
git rm backend/.env.example 2>/dev/null
git rm -r backend/.github/ 2>/dev/null
```

- [ ] **Step 2: Remove stale files from nlp-service/**

```bash
git rm nlp-service/docker-compose.dev.yml 2>/dev/null
git rm -r nlp-service/.github/ 2>/dev/null
```

- [ ] **Step 3: Commit**

```bash
git commit -m "Remove stale compose/CI/env files from subdirectories (moved to infra/)"
```

---

### Task 12.5: Replace old READMEs with redirect notes

**Files:**
- Modify: `backend/README.md` (old SpringShelf README)
- Modify: `nlp-service/README.md` (old StoryWeave README)
- Keep: `docs/backend/` and `docs/nlp-service/` (internal documentation, referenced from root README)

- [ ] **Step 1: Replace backend/README.md**

Overwrite `backend/README.md`:
```bash
cat > backend/README.md << 'READMEEOF'
# backend/ — SpringShelf

This directory is part of the **[storyshelf](https://github.com/stokuj/storyshelf)** monorepo.

Java Spring Boot backend for book tracking. For the full project overview, see the [root README](../README.md).

## Internal docs

- [API Endpoints](docs/api_endpoints.md)
- [Database Schema](docs/database.md)
- [NLP Data Flow](docs/data_flow.md)
- [User Stories](docs/user_stories.md)
- [Project Structure](docs/project_structure.md)
READMEEOF
```

- [ ] **Step 2: Replace nlp-service/README.md**

Overwrite `nlp-service/README.md`:
```bash
cat > nlp-service/README.md << 'READMEEOF'
# nlp-service/ — StoryWeave

This directory is part of the **[storyshelf](https://github.com/stokuj/storyshelf)** monorepo.

Python FastAPI microservice for NLP book analysis (NER, character extraction, LLM-based relation extraction). For the full project overview, see the [root README](../README.md).

## Internal docs

- [API Request Examples](docs/request_examples.md)
- [Testing NER Models](docs/testing_ner_models.md)
READMEEOF
```

- [ ] **Step 3: Commit**

```bash
git add backend/README.md nlp-service/README.md
git commit -m "Replace old READMEs with redirect notes to root storyshelf README"
```

---

### Task 13: Verify everything

- [ ] **Step 1: Verify directory structure**

```bash
find . -maxdepth 3 -not -path './.git/*' -not -path './backend/backend/target/*' -not -path './frontend/node_modules/*' -not -path './nlp-service/.venv/*' | sort
```
Expected: structure matches spec — `backend/`, `frontend/`, `nlp-service/`, `infra/` with their subdirs, `Makefile`, `README.md`, `.gitignore`, `.github/`.

- [ ] **Step 2: Verify full commit count from both repos**

```bash
echo "=== Commits in this monorepo ==="
echo "backend/:     $(git log --oneline -- backend/  | wc -l)"
echo "nlp-service/: $(git log --oneline -- nlp-service/ | wc -l)"
echo ""
echo "=== Commits in original repos ==="
echo "springshelf:  $(git -C /home/dv6/GitHub/BookNLP/springshelf log --oneline | wc -l)"
echo "storyweave:   $(git -C /home/dv6/GitHub/BookNLP/storyweave log --oneline | wc -l)"
```
Expected: monorepo commit counts match originals (±1-2 for merge commits). If counts differ significantly, the subtree merge was incomplete — re-run Task 1/2.

- [ ] **Step 3: Verify old READMEs replaced, docs preserved**

```bash
echo "=== Old READMEs should be redirects ==="
head -3 backend/README.md
head -3 nlp-service/README.md
echo ""
echo "=== Internal docs preserved ==="
ls docs/backend/
ls docs/nlp-service/
```
Expected: READMEs show "part of storyshelf monorepo". Docs directories contain original files.

- [ ] **Step 4: Verify Makefile targets**

```bash
make -n dev-up
make -n prod-up
make -n dev-status
```
Expected: all print the expected `docker compose` commands.

- [ ] **Step 5: Verify compose files validate**

```bash
docker compose -f infra/compose/docker-compose.dev.yml config -q 2>&1
docker compose -f infra/compose/docker-compose.prod.yml config -q 2>&1
```
Expected: `docker compose config -q` returns 0 (silent) for valid configs. If it fails, check context paths — compose resolves them relative to the compose file's location.

---

### Task 14: Push to GitHub and archive old repos

- [ ] **Step 1: Create remote repo and push**

This step requires `gh` auth. First verify the repo exists or create it:
```bash
gh repo list stokuj --json name | grep storyshelf || gh repo create stokuj/storyshelf --public --description "Full-stack book tracking and literary analysis platform"
```

Then push:
```bash
git remote add origin https://github.com/stokuj/storyshelf.git 2>/dev/null
git push -u origin main
```
Expected: push succeeds, `main` branch visible on GitHub.

- [ ] **Step 2: Archive old repos on GitHub**

```bash
gh api -X PATCH repos/stokuj/springshelf -f archived=true
gh api -X PATCH repos/stokuj/storyweave -f archived=true
```
Expected: HTTP 200, repos are now read-only on GitHub.

- [ ] **Step 3: Clean up old local repos (optional)**

```bash
# Remove .git directories from old repos to prevent confusion
rm -rf /home/dv6/GitHub/BookNLP/springshelf/.git
rm -rf /home/dv6/GitHub/BookNLP/storyweave/.git
```
Expected: old directories lose git tracking but files remain as reference.

---
