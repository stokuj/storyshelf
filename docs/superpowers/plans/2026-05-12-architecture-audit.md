# Architecture Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a fast, evidence-based audit of repository compliance with `ARCHITECTURE.md` and report the highest-priority mismatches.

**Architecture:** The audit is document-led and evidence-first. Each task verifies one architecture area against the strongest available repository sources, records a status, and captures the file references needed for a concise final report.

**Tech Stack:** OpenCode tools, ripgrep-powered search, Django/Vue/Celery repository configuration, GitHub Actions workflow files

---

## File Structure

- Reference: `ARCHITECTURE.md` — source document being audited
- Reference: `infra/compose/docker-compose.dev.yml` — development container topology
- Reference: `infra/compose/docker-compose.prod.yml` — production container topology if present
- Reference: `frontend/src/auth.js` — frontend auth state and token handling
- Reference: `frontend/src/api.js` — API request behavior and auth refresh behavior
- Reference: `frontend/src/router/` or `frontend/src/router.js` — auth initialization flow
- Reference: `backend-django/config/settings/base.py` — shared Django settings
- Reference: `backend-django/config/settings/dev.py` — dev-only runtime behavior
- Reference: `backend-django/config/settings/prod.py` — prod-only runtime behavior
- Reference: `backend-django/config/celery.py` and related task modules — Celery topology and routing
- Reference: `backend-django/**/models.py` — database and domain model verification
- Reference: `.github/workflows/ci.yml` — CI/CD verification
- Output: chat response only — final audit table and high-priority mismatches

### Task 1: Verify Stack And Active Runtime Components

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `frontend/package.json`
- Read: `backend-django/pyproject.toml`
- Read: `infra/compose/docker-compose.dev.yml`
- Read: `infra/compose/docker-compose.prod.yml` if it exists

- [ ] **Step 1: Read the architecture stack claims**

Read `ARCHITECTURE.md` and note claims about frontend, backend, auth, broker, result backend, workers, monitoring, database, reverse proxy, CI/CD, and deployment.

- [ ] **Step 2: Verify frontend and backend runtime technologies**

Check `frontend/package.json` and `backend-django/pyproject.toml` for evidence that the repo uses Vue 3, Vite, Django, DRF, and the expected supporting packages.

- [ ] **Step 3: Verify infrastructure service presence**

Inspect `infra/compose/docker-compose.dev.yml` and `infra/compose/docker-compose.prod.yml` if present to confirm whether PostgreSQL, Redis, RabbitMQ, Flower, frontend, backend, and reverse proxy services exist as claimed.

- [ ] **Step 4: Record stack status**

For the final report, assign one status for the stack/runtime area and keep the strongest file references that justify it.

### Task 2: Verify Container Topology And Data Flow

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `infra/compose/docker-compose.dev.yml`
- Read: `infra/compose/docker-compose.prod.yml` if it exists
- Read: `frontend/vite.config.*`
- Read: reverse proxy config under `infra/` or project root

- [ ] **Step 1: Extract the container and routing claims**

From `ARCHITECTURE.md`, list the expected dev/prod flow, especially frontend proxy behavior, backend routing, and reverse proxy responsibilities.

- [ ] **Step 2: Verify development topology**

Check `infra/compose/docker-compose.dev.yml` for actual service names, mounts, ports, dependencies, and whether dev uses Vite directly or a containerized Nginx frontend.

- [ ] **Step 3: Verify production topology and reverse proxy behavior**

Inspect `infra/compose/docker-compose.prod.yml` if present and the reverse proxy configuration to confirm SSL termination and request routing responsibilities.

- [ ] **Step 4: Record topology/data-flow status**

Keep the clearest evidence for whether the documented request path matches the real configuration.

### Task 3: Verify Authentication Model

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `frontend/src/auth.js`
- Read: `frontend/src/api.js`
- Read: frontend router file responsible for auth initialization
- Read: backend auth views, serializers, and URL config under `backend-django/`

- [ ] **Step 1: Extract auth claims from the architecture document**

Note the expected access-token storage, refresh-token storage, refresh behavior, and named endpoints.

- [ ] **Step 2: Verify frontend token handling**

Confirm from `frontend/src/auth.js` and `frontend/src/api.js` whether the access token lives in memory, whether refresh uses cookies, and how 401 refresh flow is handled.

- [ ] **Step 3: Verify backend auth endpoints**

Inspect backend auth URLs and views to confirm whether `register`, `login`, `token/refresh`, `logout`, and current-user endpoints exist and align with the document.

- [ ] **Step 4: Record auth status**

Capture the main file references and classify the area without inferring behavior not backed by code.

### Task 4: Verify Celery Workers, Queues, And Failure Handling

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `infra/compose/docker-compose.dev.yml`
- Read: `backend-django/config/settings/base.py`
- Read: Celery app and task routing files in `backend-django/`
- Read: `infra/rabbitmq/definitions.json`

- [ ] **Step 1: Extract async-processing claims**

List the documented worker types, queue names, concurrency model, result backend, retry behavior, and dead-letter behavior.

- [ ] **Step 2: Verify worker services and pool settings**

Use `infra/compose/docker-compose.dev.yml` to confirm whether separate `celery-ner` and `celery-llm` services exist and whether their command lines match the documented pools.

- [ ] **Step 3: Verify task routing and backend settings**

Inspect Celery configuration and task modules to confirm queue routing, broker backend configuration, and whether Redis and RabbitMQ are wired as the document claims.

- [ ] **Step 4: Verify dead-letter setup**

Check `infra/rabbitmq/definitions.json` or equivalent configuration for dead-letter exchange and queue definitions.

- [ ] **Step 5: Record Celery status**

Summarize whether the async architecture claims are fully supported, partially supported, or contradicted by config.

### Task 5: Verify Database And Domain Model Claims

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `backend-django/books/models.py`
- Read: `backend-django/library/models.py`
- Read: other model files referenced by URLs or app structure

- [ ] **Step 1: Extract key schema claims**

From `ARCHITECTURE.md`, note the expected `Book`, `Review`, `ShelfEntry`, `Serie`, chapter analysis, entity tables, and relationship model structure.

- [ ] **Step 2: Verify book-related models**

Inspect `books/models.py` for the real fields and relations on `Book`, `Review`, `ShelfEntry`, `Chapter`, and `CharacterRelationship`.

- [ ] **Step 3: Verify library and entity models**

Inspect `library/models.py` and any analysis/entity model modules to confirm whether `Serie`, `Genre`, `Author`, and global entity tables match the document.

- [ ] **Step 4: Record schema status**

Capture only the most material mismatches that affect the validity of `ARCHITECTURE.md`.

### Task 6: Verify CI/CD Claims

**Files:**
- Read: `ARCHITECTURE.md`
- Read: `.github/workflows/ci.yml`
- Read: deployment-related compose files or scripts if referenced by workflow

- [ ] **Step 1: Extract CI/CD claims**

List the documented path from push, to tests, to image build, to GHCR, to VPS deployment.

- [ ] **Step 2: Verify the workflow implementation**

Inspect `.github/workflows/ci.yml` for linting, tests, Docker build, image push, and deployment steps, including any commented or inactive sections.

- [ ] **Step 3: Record CI/CD status**

Classify the area based on the actual workflow behavior, not the intended roadmap.

### Task 7: Produce The Final Audit Report

**Files:**
- Read: notes gathered from Tasks 1-6
- Reference: `docs/superpowers/specs/2026-05-12-architecture-audit-design.md`

- [ ] **Step 1: Normalize statuses across all areas**

Ensure every audited area uses one of the approved statuses: `zgodne`, `częściowo zgodne`, `niezgodne`, `niezweryfikowane`.

- [ ] **Step 2: Draft the audit table**

Create a compact table with columns `Area`, `Status`, `Evidence`, and `Finding`.

- [ ] **Step 3: Extract highest-priority mismatches**

List only the most important mismatches after the table. Prefer items that change how someone understands or operates the system.

- [ ] **Step 4: Final verification before reporting**

Re-check every mismatch against the cited files so the report does not overstate certainty.
