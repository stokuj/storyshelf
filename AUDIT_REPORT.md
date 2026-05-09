# AUDIT REPORT: storyshelf monorepo

**Date:** 2026-05-09
**Branch:** `audit/full-project-review`
**Repo:** https://github.com/stokuj/storyshelf

## Summary

| | Count |
|---|---|
| Bugs (critical — fix before prod) | 16 |
| Warnings (important — fix soon) | 26 |
| Suggestions (nice-to-have) | 34 |
| Tests (backend) | 239 run, 0 fail ✅ |
| Integration contract (Kafka) | 4 topics matched ✅ |

**Overall code quality:** 6/10 — solid architecture, Kafka contract is sound, tests pass, but multiple P0 blocking bugs in production path (Caddy routing, security, race conditions) and documentation is stale.

**Biggest risk:** Caddyfile points to wrong service name → NLP service unreachable in production.

**Top 3 actions:**
1. Fix Caddyfile `storyweave-api` → `nlp-service`
2. Fix CORS `*` + `allowCredentials(true)` 
3. Fix LoginView email-as-username bug

---

## P0 — Blocking Production

### [BUG] Caddy routing to wrong service name
Caddyfile reverse_proxy targets `storyweave-api:8000` but docker-compose.prod.yml service is named `nlp-service`. Docker DNS resolves by service name, not container_name. NLP service is unreachable in prod.
- **File:** `infra/caddy/Caddyfile:4,9,13,34`
- **Fix:** Change `storyweave-api:8000` → `nlp-service:8000` everywhere in Caddyfile

### [BUG] Kafka consumer never commits offset for 'book.relations' topic  
Every restart re-processes ALL book.relations messages. Missing `consumer.commit()` in the `elif` block.
- **File:** `nlp-service/api/kafka/consumer.py:85-100`

### [BUG] CORS wildcard + credentials = CSRF risk
`setAllowedOriginPatterns("*")` + `setAllowCredentials(true)` allows any origin to send session cookies on credentialed requests.
- **File:** `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java:84-88`

### [BUG] Login sends email as username
LoginView sends `form.email` as field name `username` to POST `/api/auth/login`. Users who register with a different username than email cannot log in.
- **File:** `frontend/src/views/LoginView.vue:68`

### [BUG] NLP docs paths completely wrong
`REQUEST_EXAMPLES.md` shows `/analyse/`, `/ner/` etc. but routers use `/chapters/{chapterId}/analyse`, `/chapters/{chapterId}/ner`.
- **File:** `nlp-service/docs/REQUEST_EXAMPLES.md` (entire file)

### [BUG] Stale logout endpoint documented but not implemented
`api_endpoints.md` lists `POST /api/auth/logout` but AuthController has no such endpoint.
- **File:** `backend/docs/api_endpoints.md:12`

---

## P1 — Breaking Features

### [BUG] NER race condition
`NerResultProcessor.process()` reads `book.nerCompletedCount`, increments locally, saves — not atomic. Two concurrent NER results for same book → wrong count, `find-pairs` never triggered.
- **File:** `backend/backend/src/main/java/com/stokuj/books/integration/processor/NerResultProcessor.java:50`

### [BUG] Relations dedup drops partial batch results
`hasResolvedRelations` check skips ALL relations results if ANY single relation already has non-null relation string. Partial batches silently dropped.
- **File:** `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java:140-146`

### [BUG] BookDetailView blank page for non-existent book
No `v-else` fallback when `details` is null after loading.
- **File:** `frontend/src/views/BookDetailView.vue:8-213`

### [BUG] ProfileView blank page for non-existent user
Same issue as BookDetailView — no fallback when `profile` is null.
- **File:** `frontend/src/views/ProfileView.vue:6-58`

### [BUG] Celery relations_task defined but never dispatched
Registered in celery config's `include` but never called via `.delay()`. Dead code.
- **File:** `nlp-service/api/tasks/relations_task.py:9-18`

### [BUG] Relations router accepts empty pairs silently
No validation for empty `pairs` list → async task processes nothing.
- **File:** `nlp-service/api/routers/relations.py:22-26`

### [BUG] Analyse router blocks event loop
Calls synchronous `process_analyse` directly in async context without offloading.
- **File:** `nlp-service/api/routers/analyse.py:23`

### [BUG] Analyse response silently ignores missing fields
`charCount` set to null if both `char_count` and `charCount` missing in Kafka payload. No validation, no error logged.
- **File:** `backend/backend/src/main/java/com/stokuj/books/integration/kafka/AnalysisResultConsumer.java:69-72`

### [BUG] ChapterEventProducer sends raw List<?> to Kafka
`PairResult` Java records serialized without explicit serializer → unexpected JSON field names.
- **File:** `backend/backend/src/main/java/com/stokuj/books/integration/kafka/ChapterEventProducer.java:56-64`

---

## P2 — Quality / Code Smells

### [BUG] Frontend has no health endpoint
Unlike backend (Spring Actuator) and NLP (`/health/`), frontend has no healthcheck route. Container probes will fail.
- **File:** `frontend/` (missing)

---

## Warnings

### Security
- [WARN] HSTS disabled (httpStrictTransportSecurity.disable()) — should be on in prod • `backend/backend/src/main/java/com/stokuj/books/security/SecurityConfig.java:30-31`
- [WARN] Generic Exception handler exposes `ex.getMessage()` to clients — may leak internals • `backend/backend/src/main/java/com/stokuj/books/exception/GlobalExceptionHandler.java:52-59`
- [WARN] Kafka port 9092 exposed on host in prod compose — no 127.0.0.1 binding • `infra/compose/docker-compose.prod.yml:119-120`
- [WARN] Hardcoded 'secret-key' password default in 4 places — easy to forget • `.env.example`, both compose files

### Data Integrity
- [WARN] No @Version on User entity — concurrent profile updates silently overwrite • `backend/backend/src/main/java/com/stokuj/books/user/User.java:11`
- [WARN] @Transactional on @KafkaListener — at-least-once vs exactly-once gap • `AnalysisResultConsumer.java:45,77,104,126`
- [WARN] IllegalStateException thrown 4x in Kafka consumer with no @ExceptionHandler — relies on DLT • `AnalysiResultConsumer.java:56,88,115,137`

### NLP Service
- [WARN] Integration tests lack @pytest.mark.integration markers — run during unit tests • `test/integration/`
- [WARN] Kafka producer module-level singleton created before dotenv loaded • `nlp-service/api/kafka/producer.py:15`
- [WARN] SENTENCE_SPLIT_REGEX fails on abbreviations (Mr., Dr., ...) • `nlp-service/api/services/core/text_parser.py:6`
- [WARN] tiktoken fallback `len(text)//4` inaccurate for non-English • `nlp-service/api/services/core/text_stats.py:27`
- [WARN] LLM API errors silently return empty relations — swallows auth/timeout errors • `nlp-service/api/services/core/llm_engine.py:139-146,173-180`

### Frontend
- [WARN] Redundant `refreshAuth()` call — App.vue onMounted + router.beforeEach both trigger • `frontend/src/views/App.vue:38-40`
- [WARN] Admin views share single `saving` boolean — disables ALL rows' buttons simultaneously • `frontend/src/views/admin/AdminBooksView.vue:160`
- [WARN] No global HTTP error interceptor — every view duplicates same try/catch pattern • `frontend/src/api.js:18-48`

### Infrastructure
- [WARN] Backend Dockerfile has suboptimal COPY order (no dependency layer caching) • `backend/backend/Dockerfile:3-5`
- [WARN] nlp-service Dockerfile is single-stage — build-essential stays in final image • `nlp-service/Dockerfile:8`
- [WARN] appleboy/ssh-action@v1.0.3 outdated (current v1.3.0) • `.github/workflows/ci.yml:122`

### Documentation / Config
- [WARN] data_flow.md documents only chapter.analyse and chapter.ner, omits book.find-pairs and book.relations • `backend/docs/data_flow.md:9-11`
- [WARN] AnalyseResponse/AnalyseStats DTOs defined but never used for Kafka deserialization • `integration/dto/AnalyseResponse.java`
- [WARN] spring-boot-starter-webflux in pom.xml but no WebClient usage found • `backend/backend/pom.xml:102-103`
- [WARN] Celery/MRP/BSE env vars hardcoded in compose `environment:` blocks (not `${VAR}` refs) • both compose files
- [WARN] No request logging middleware in FastAPI • `nlp-service/api/app.py:83-94`
- [WARN] No logging config in Spring Boot application.yml • `backend/backend/src/main/resources/application.yml`

---

## Suggestions (34 total)

Selected highlights:
- [SUG] Replace session auth with JWT for REST API scalability • `SecurityConfig.java:34`
- [SUG] Use typed DTO deserialization instead of raw `Map<String,Object>` in Kafka consumers
- [SUG] Add @Min(1) @Max(5) validation on Review.rating field • `Review.java:33`
- [SUG] Add ISBN format validation in Book entity/controller
- [SUG] Add 404 catch-all route in Vue router
- [SUG] Add `useErrorBoundary` composable for DRY error/loading states in .vue files
- [SUG] Split Dockerfile COPY for better caching (pom.xml deps → src)
- [SUG] Bind Kafka to 127.0.0.1 in prod compose
- [SUG] Add healthcheck to nlp-service in prod compose
- [SUG] Add deploy.sh `--dry-run` flag
- [SUG] Add logging config to application.yml
- [SUG] Add ASGI middleware for FastAPI access logging
- [SUG] Add frontend /health route for Docker probes
- [SUG] Remove dead spring-boot-starter-webflux, celery-types runtime dep
- [SUG] Hibernate 6.x JSON mapping for Java records should be tested across DB dialects

---

## Module-by-Module Detail

### Module 1: Backend (Spring Boot)
- Tests: ✅ 239 pass, 0 fail
- 5 bugs, 6 warnings, 8 suggestions
- Cleanest module — tests pass, Kafka integration structurally correct
- Main issues: CORS security, atomic counters in NER processor, dedup logic

### Module 2: Frontend (Vue 3)
- 3 bugs, 3 warnings, 4 suggestions
- Missing null/empty states in 2 views, login payload mismatch, redundant auth
- All admin views are well-structured

### Module 3: nlp-service (Python FastAPI)
- 4 bugs, 5 warnings, 6 suggestions
- Kafka commit bug for relations topic is critical
- Sentence split regex is too simple — will fail on real books
- Integration tests incorrectly marked — run as unit tests

### Module 4: Infrastructure
- 1 bug, 4 warnings, 5 suggestions
- **Caddy routing bug is P0** — NLP service won't work in prod
- Compose files validate cleanly, CI structure is sound

### Module 5: Integration Spring ↔ FastAPI
- 0 bugs, 3 warnings, 3 suggestions
- **All 4 Kafka topic pairs match exactly** ✅
- JSON key formats compatible (snake_case ↔ Map access)
- No field name mismatches — the contract is solid

### Module 6: General Gaps
- 3 bugs, 5 warnings, 8 suggestions
- Documentation is stale (REQUEST_EXAMPLES paths, logout in api_endpoints)
- Missing health endpoints, logging configs
- Unused dependency (spring-boot-starter-webflux)
