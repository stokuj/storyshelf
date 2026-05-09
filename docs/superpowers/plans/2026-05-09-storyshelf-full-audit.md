# Pełny Audyt Monorepo storyshelf — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Przeprowadzić pełny audyt kodu monorepo storyshelf (backed, frontend, nlp-service, infra, integracja, luki) i wygenerować raport z listą bugów, ostrzeżeń i sugestii.

**Architecture:** 6 modułów audytowych, każdy jako osobny subagent z precyzyjną checklistą. Subagenty czytają kod, uruchamiają testy, porównują kontrakty, zwracają raporty. 7. subagent składa wszystko w jeden plik `AUDIT_REPORT.md`.

**Tech Stack:** Java/Spring Boot, Vue 3, Python/FastAPI, Docker Compose, Caddy, Kafka, Celery, GitHub Actions

**Branch:** `audit/full-project-review`

---

### Task 1: Audyt Backendu (Spring Boot)

**Files to audit:**
- All `backend/backend/src/main/java/com/stokuj/books/**/*.java`
- All `backend/backend/src/test/java/com/stokuj/books/**/*.java`
- `backend/backend/pom.xml`
- `backend/backend/src/main/resources/application.yml`
- `backend/backend/src/main/resources/application-dev.yml`
- `backend/backend/Dockerfile`
- `backend/.env.example`

- [ ] **Step 1: Map controllers and endpoints**

List all controllers and their endpoints. Run and examine:
```bash
grep -rn "@RestController\|@RequestMapping\|@GetMapping\|@PostMapping\|@PutMapping\|@PatchMapping\|@DeleteMapping" backend/backend/src/main/java/ --include="*.java"
```

- [ ] **Step 2: Run Java tests**

```bash
cd backend/backend && mvn -B test 2>&1 | tail -30
```
Note: If Maven not installed, skip and note as [WARN] — tests cannot be verified.

- [ ] **Step 3: Check Kafka integration**

Read and compare:
- `backend/backend/src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java` — what topic does it produce to? What data?
- `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java` — what topic does it consume from? What DTO classes?
- `backend/backend/src/main/java/com/stokuj/books/config/KafkaConfig.java` — what topics are configured?

- [ ] **Step 4: Check exception handling**

Read and analyze:
- `backend/backend/src/main/java/com/stokuj/books/exception/GlobalExceptionHandler.java` — what exceptions are caught? What HTTP statuses returned? What JSON format?

- [ ] **Step 5: Check security config**

Read and analyze:
- `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java` — public vs protected endpoints, CORS, JWT filter
- `backend/backend/src/main/java/com/stokuj/books/config/OpenApiConfig.java` — Swagger accessible?

- [ ] **Step 6: Check DTOs for consistency**

Read all files in `backend/backend/src/main/java/com/stokuj/books/integration/dto/` and check:
- Are `@JsonProperty` or field names consistent with what nlp-service sends (snake_case vs camelCase)?
- Does each DTO have getters/setters or use records?

- [ ] **Step 7: Check entities for Lombok or manual getters/setters**

Run:
```bash
grep -rn "@Entity\|@Data\|@Getter\|@Setter" backend/backend/src/main/java/com/stokuj/books/ --include="*.java" | head -30
```
Check if entities use `@Data` (Lombok) or manual getters/setters. If neither, that's a [BUG] — controller/service won't compile.

- [ ] **Step 8: Produce findings report**

Write findings to an intermediate file (for later synthesis):
```
AUDIT Module 1: Backend (Spring Boot)

Bugs:
- [BUG] description • file:line • cause
...
Warnings:
- [WARN] description • file:line
...
Suggestions:
- [SUG] description • file:line
```

---

### Task 2: Audyt Frontendu (Vue 3)

**Files to audit:**
- `frontend/src/router.js`
- `frontend/src/api.js`
- `frontend/src/auth.js`
- `frontend/src/main.js`
- All `frontend/src/views/**/*.vue`
- `frontend/vite.config.js`

- [ ] **Step 1: Map routes and components**

Read `frontend/src/router.js` and list every route path → component mapping.

- [ ] **Step 2: Map API endpoints**

Read `frontend/src/api.js` and list every API endpoint called (method + path). Compare against backend endpoints from Task 1 Step 1.

- [ ] **Step 3: Check auth flow**

Read `frontend/src/auth.js` and trace the auth flow: 
- Where is token stored?
- How is token attached to requests?
- Is there token refresh logic?

- [ ] **Step 4: Check view states**

For EACH view under `frontend/src/views/`, check:
- Does it handle loading state? (spinner/skeleton while API fetches)
- Does it handle empty state? (no data message)
- Does it handle error state? (error message display)
- Does it handle data state? (normal rendering)

List any view that's missing one of these states.

- [ ] **Step 5: Check vite proxy config**

Read `frontend/vite.config.js` — does the proxy target match the backend host:port?

- [ ] **Step 6: Produce findings report**

```
AUDIT Module 2: Frontend (Vue 3)

Bugs:
...
Warnings:
...
Suggestions:
...
```

---

### Task 3: Audyt nlp-service (Python FastAPI)

**Files to audit:**
- All `nlp-service/api/**/*.py`
- All `nlp-service/test/**/*.py`
- `nlp-service/Dockerfile`
- `nlp-service/pyproject.toml`

- [ ] **Step 1: Run Python tests**

```bash
cd nlp-service
uv run pytest -v -m "not integration" 2>&1 | tail -40
```
Capture: pass/fail count, coverage if available.

- [ ] **Step 2: Run coverage report**

```bash
cd nlp-service
uv run coverage run -m pytest -m "not integration" 2>/dev/null
uv run coverage report --include="api/*" 2>/dev/null || echo "coverage not installed or failed"
```

- [ ] **Step 3: Check Kafka consumer/producer topics**

Read:
- `nlp-service/api/kafka/consumer.py` — what topic? What message format expected?
- `nlp-service/api/kafka/producer.py` — what topic? What message format sent?
- Compare topic names against Spring Kafka config from Module 1.

- [ ] **Step 4: Check Celery tasks and workflow chain**

Read all files in `nlp-service/api/tasks/` and `nlp-service/api/services/workflows/`.
Trace: from Kafka consumer message → which tasks fire → what order → what result is produced back to Kafka.

- [ ] **Step 5: Check endpoint routers**

Read each file in `nlp-service/api/routers/` and list:
- Endpoint path, HTTP method
- Required parameters
- Response model

- [ ] **Step 6: Check service implementations**

Read each file in `nlp-service/api/services/core/` and check:
- `llm_engine.py` — which LLM model, how called, error handling
- `transformers_engine.py` — which NER model, batching
- `text_parser.py` — chapter/sentence splitting

- [ ] **Step 7: Check Dockerfile**

Read `nlp-service/Dockerfile` — is it using uv sync correctly? Cache layers?

- [ ] **Step 8: Check refactor.py**

Read `nlp-service/refactor.py` — is it dead code? One-off script? Should it be removed?

- [ ] **Step 9: Produce findings report**

```
AUDIT Module 3: nlp-service (Python FastAPI)

Bugs:
...
Warnings:
...
Suggestions:
...
```

---

### Task 4: Audyt Infrastruktury

**Files to audit:**
- `infra/compose/docker-compose.dev.yml`
- `infra/compose/docker-compose.prod.yml`
- `infra/caddy/Caddyfile`
- `.github/workflows/ci.yml`
- `Makefile`
- `backend/backend/Dockerfile`
- `frontend/Dockerfile`
- `frontend/Dockerfile.prod`
- `nlp-service/Dockerfile`
- `.gitignore`

- [ ] **Step 1: Validate dev compose**

```bash
cp infra/.env.example .env 2>/dev/null || true
docker compose -f infra/compose/docker-compose.dev.yml config -q 2>&1; echo "exit: $?"
```
If fails, capture error output.

- [ ] **Step 2: Validate prod compose**

```bash
docker compose -f infra/compose/docker-compose.prod.yml config -q 2>&1; echo "exit: $?"
```

- [ ] **Step 3: Check compose service dependencies**

In each compose file, check for each `depends_on`:
- Does the referenced service exist in the compose file?
- Is `condition: service_healthy` used where the service has a healthcheck?

- [ ] **Step 4: Check Caddyfile routing**

Read `infra/caddy/Caddyfile` and for each `reverse_proxy` directive:
- Does the service name match a service in prod compose?
- Is the port correct?

- [ ] **Step 5: Check CI/CD**

Read `.github/workflows/ci.yml` and:
- Are all action versions current?
- Does `working-directory` point to existing paths?
- Do image names in `build-and-push` match image names in `docker-compose.prod.yml`?
- Is the deploy SSH action configured correctly (uses `secrets.GCP_*`)?

- [ ] **Step 6: Validate Makefile**

```bash
for target in dev-up dev-down dev-status prod-up prod-down prod-status prod-logs; do
  echo "=== $target ==="
  make -n $target 2>&1
done
```

- [ ] **Step 7: Check Dockerfiles**

Read each Dockerfile and check:
- Are they multi-stage where beneficial?
- Are there any `COPY . .` that would include node_modules/.venv?
- Are `.dockerignore` files present?

- [ ] **Step 8: Check .gitignore completeness**

Read `.gitignore` and check if it covers:
- `*.env` (security)
- Build artifacts for each module
- IDE configs

- [ ] **Step 9: Produce findings report**

```
AUDIT Module 4: Infrastructure

Bugs:
...
Warnings:
...
Suggestions:
...
```

---

### Task 5: Audyt Integracji Spring ↔ FastAPI

**Files to audit (compare sides):**
- Spring: `backend/backend/src/main/java/com/stokuj/books/integration/kafka/*.java`
- Spring: `backend/backend/src/main/java/com/stokuj/books/integration/dto/*.java`
- FastAPI: `nlp-service/api/kafka/consumer.py`
- FastAPI: `nlp-service/api/kafka/producer.py`
- FastAPI: `nlp-service/api/models/model.py`
- FastAPI: `nlp-service/api/tasks/*.py`
- Docs: `backend/docs/data_flow.md`

- [ ] **Step 1: Map Kafka topics — Spring producer side**

Read `ChapterEventProducer.java`. Extract:
- Topic name
- Message type/structure sent
- When messages are sent (which controller/service triggers it)

- [ ] **Step 2: Map Kafka topics — FastAPI consumer side**

Read `nlp-service/api/kafka/consumer.py`. Extract:
- Topic subscribed to
- Message format expected (JSON keys)
- What happens when a message arrives (which Celery task)

- [ ] **Step 3: Compare topic names**

Do Spring producer topic names match FastAPI consumer topic names? If not — [BUG].

- [ ] **Step 4: Map Kafka topics — FastAPI producer side**

Read `nlp-service/api/kafka/producer.py`. Extract:
- Topic name
- Message structure sent

- [ ] **Step 5: Map Kafka topics — Spring consumer side**

Read `AnalysisResultConsumer.java`. Extract:
- Topic subscribed to
- Message format expected (JSON keys → DTO mapping)

- [ ] **Step 6: Compare response topics**

Do FastAPI producer topics match Spring consumer topics? If not — [BUG].

- [ ] **Step 7: Compare JSON key formats (snake_case vs camelCase)**

Check if Spring uses `@JsonProperty("ner_results")` with snake_case, and if FastAPI produces snake_case keys. Mismatch = [BUG].

- [ ] **Step 8: Read data flow documentation**

Read `backend/docs/data_flow.md` — does it accurately describe the actual code flow? Document any discrepancies.

- [ ] **Step 9: Produce findings report**

```
AUDIT Module 5: Integration Spring ↔ FastAPI

Bugs:
...
Warnings:
...
Suggestions:
...
```

---

### Task 6: Audyt Luk Ogólnych

**Files to audit:**
- `README.md`, `backend/README.md`, `nlp-service/README.md`
- `backend/docs/data_flow.md`, `backend/docs/api_endpoints.md`
- `nlp-service/docs/REQUEST_EXAMPLES.md`
- `infra/.env.example`
- `backend/backend/pom.xml`, `nlp-service/pyproject.toml`, `frontend/package.json`
- All `docker-compose*.yml` (for env var references)

- [ ] **Step 1: Security check — env vars with secrets**

Search all compose files for env vars that contain keys/tokens/passwords:
```bash
grep -n "KEY\|TOKEN\|SECRET\|PASSWORD" infra/compose/docker-compose.dev.yml infra/compose/docker-compose.prod.yml backen/../Caddyfile 2>/dev/null || true
grep -n "KEY\|TOKEN\|SECRET\|PASSWORD" nlp-service/api/config/settings.py
```
Are defaults exposed? Are secrets properly in env_file?

- [ ] **Step 2: CORS check in prod**

Check `nlp-service/api/app.py` or `nlp-service/api/config/settings.py` for CORS configuration. Is `CORS_ALLOW_ORIGINS` set to `*` in any profile that could go to prod?

- [ ] **Step 3: Documentation vs actual code consistency**

Read `README.md` — do all listed endpoints/ports match what's in compose files?
Read `backend/docs/api_endpoints.md` — sample 3 endpoints, do they exist in controllers?
Read `nlp-service/docs/REQUEST_EXAMPLES.md` — do paths match actual router paths?

- [ ] **Step 4: Unused dependencies**

Check each dependency file:
- `backend/backend/pom.xml` — any dependency not imported anywhere?
- `nlp-service/pyproject.toml` — any dependency not imported in api/?
- `frontend/package.json` — any dependency not imported in src/?

Run: 
```bash
cd nlp-service && uv run pipdeptree 2>/dev/null || echo "pipdeptree not available"
```

- [ ] **Step 5: Health checks**

Search all services for health endpoints:
```bash
grep -rn "health\|/health\|actuator" backend/backend/src/main/ nlp-service/api/ frontend/src/ 2>/dev/null
```
Do all services have health endpoints? Are they used in compose healthchecks?

- [ ] **Step 6: Monitoring/logging**

Check if logging is configured in:
- Spring: application.yml (logging level)
- FastAPI: app.py (logging middleware)
- Caddyfile: log directive

- [ ] **Step 7: Environment variable completeness**

Read `infra/.env.example` — list all vars. Read all compose files — list all env vars used. Are there vars used in compose but not documented in .env.example? Or vice versa?

- [ ] **Step 8: Produce findings report**

```
AUDIT Module 6: General Gaps

Bugs:
...
Warnings:
...
Suggestions:
...
```

---

### Task 7: Synteza raportu końcowego

**Files:**
- Create: `AUDIT_REPORT.md` (root level, on audit branch)

- [ ] **Step 1: Combine all module reports**

Collect findings from Tasks 1-6. Create `AUDIT_REPORT.md` with this structure:

```markdown
# AUDIT REPORT: storyshelf monorepo
**Date:** 2026-05-09
**Branch:** audit/full-project-review

## Summary
- Total Bugs: X
- Total Warnings: X
- Total Suggestions: X

## Bugs (Critical — must fix before prod)
[All [BUG] items from all modules, sorted by severity]

## Warnings (Important — fix soon)
[All [WARN] items]

## Suggestions (Nice-to-have)
[All [SUG] items]

## Module-by-Module Detail
[Each module's full report]
```

- [ ] **Step 2: Prioritize**

Group bugs into:
- **P0 (Blocking production)** — security, data loss, Kafka contract mismatch
- **P1 (Breaking features)** — tests failing, compilation errors, wrong endpoints
- **P2 (Quality)** — missing states, code smells

- [ ] **Step 3: Add overall assessment**

Add a final section with:
- Overall code quality (1-10)
- Biggest risk
- Recommended next 3 actions

- [ ] **Step 4: Commit**

```bash
git add AUDIT_REPORT.md
git commit -m "Add full monorepo audit report"
```

---
