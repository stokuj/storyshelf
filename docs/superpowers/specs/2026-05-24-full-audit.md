# Spec: Full Backend + Frontend + API Contract Audit

**Date:** 2026-05-24
**Branch:** `audit/full-backend-frontend-api` (from `main`)
**Status:** Design approved

---

## Goal

Independent, documentation-only audit of StoryShelf application logic. Three objectives:

1. **Find bugs** before production deployment
2. **Verify Svelte migration** correctness (API consumption, auth flow)
3. **Overall code health assessment** (tech debt, test gaps, ADR deviations)

No code changes — output is a report only.

---

## Scope

**In:** Application logic only. Backend models, views, serializers, URL routing, auth flow. Frontend components, API client, types, auth hooks. API contract cross-reference.

**Out:** Infrastructure (Docker, Caddy, CI/CD, RabbitMQ), NLP pipeline internals (Celery workers, chunking, LLM engine), Django settings except auth/CORS.

---

## Audit Team — 11 subagents

### Inspection agents (Phase 1, parallel)

| # | Agent | Files |
|---|-------|-------|
| 1 | **Auth & Users** | `users/` — `cookie_auth.py`, `views.py`, `serializers.py`, `models.py`, `exporters.py`, `urls/*.py`, `tests/` (25 files) |
| 2 | **Books & Library** | `books/` + `library/` — `models.py`, `views.py`, `serializers.py`, `urls.py`, `lookups.py`, `tests/` (30 files) |
| 3 | **Reviews & Signals** | `reviews/` — `models.py`, `views.py`, `serializers.py`, `signals.py`, `urls.py`, `tests/` (13 files) |
| 4 | **Shelf & Collections** | `shelf/` — `models.py`, `views.py`, `serializers.py`, `urls.py`, `tests/` (11 files) |
| 5 | **Analysis & Entities** | `analysis/` — `models.py`, `views.py`, `serializers.py`, `urls.py`, `tests/test_models.py`, `tests/test_views.py` (10 application files) |
| 6 | **Frontend Auth & API** | `src/hooks.server.ts`, `src/lib/api/_client.ts`, `src/lib/api/user.ts` (3 files) |
| 7 | **Frontend UI & Routes** | `src/routes/+layout.svelte`, `src/routes/+page.svelte`, `src/routes/+page.server.ts`, `src/app.html`, `src/app.css`, `src/lib/config.ts`, `src/lib/utils.ts` (7 files) |
| 8 | **API Contract** | All `*urls.py` + `src/lib/types/api.generated.ts` + `src/lib/api/user.ts` |

Each inspection agent checks:
- Correctness (bugs, logic errors)
- ADR compliance (does code match decisions?)
- Error handling (missing try/catch, missing 4xx/5xx responses)
- Permission checks (right classes on right views)
- N+1 query potential (missing `select_related`/`prefetch_related`)
- Test coverage (what's tested, what's missing)

### Meta-analysis agents (Phase 2, parallel)

| # | Agent | Perspective | Input |
|---|-------|-------------|-------|
| 9 | **Architecture Critic** | 2 opinions: defense of current architecture AND counter-arguments | Entire codebase + all ADRs |
| 10 | **Architect** | Dead code detection, pattern quality assessment, structural coherence | Entire codebase |
| 11 | **Overengineering Detector** | YAGNI violations, unnecessary abstractions, gold-plating | Entire codebase |

### Orchestrator (Phase 3)

Collects all agent outputs, deduplicates findings, unifies severity across agents, and writes the final report.

---

## Severity Classification

| Level | Definition |
|-------|-----------|
| **Critical** | Deployment-blocking bug, security vulnerability, data loss, silent auth bypass |
| **High** | Architectural flaw, missing critical error handling, API contract mismatch causing runtime errors, ADR violation with security implications |
| **Medium** | Missing tests on important paths, N+1 query, minor ADR deviation, missing error state in UI |
| **Low** | Code style inconsistency, naming issues, dead imports, minor TODOs |

---

## Output Format

File: `docs/audits/2026-05-24-full-audit.md`

```
# StoryShelf Independent Audit — 2026-05-24

## 1. Executive Summary

## 2. Critical Issues

## 3. High Issues

## 4. Medium Issues

## 5. Low Issues

## 6. API Contract Matrix
| Endpoint | Backend Route | Frontend Call | Status |

## 7. ADR Compliance
| ADR | Decision | Code Match | Notes |

## 8. Architecture Critique
### Defense of Current State
### Counter-arguments & Alternatives

## 9. Architect's Notes
### Dead Code
### Pattern Quality
### Structural Observations

## 10. Overengineering Report

## 11. Metrics
- Python files: N | Test files: N (coverage %)
- Svelte files: N | TS files: N
- Endpoints documented in API: N
- Endpoints with missing frontend calls: N
- Dead code instances: N
- Overengineering instances: N

## 12. Priority Recommendations (top 10)
```

---

## Per-Agent Input Brief

### Agent 1 — Auth & Users
All files in `backend-django/users/`:
- `cookie_auth.py` — JWTCookieAuthentication class logic
- `views.py` — all 15+ views (Register, Login, Logout, TokenRefresh, AuthMe, UserMe, PasswordChange, EmailChange, AvatarUpload, UserSettings, DataExport, AccountDelete, UserProfile, UserFollow, FollowList, PublicShelves, RecentlyRead)
- `serializers.py` — all 11 serializers, field validation, create/update logic
- `models.py` — User (AbstractBaseUser), UserFollow, constraints
- `exporters.py` — GDPR data export
- `urls/auth.py`, `urls/users.py`, `urls/public.py`
- `tests/` — all 12 test files

### Agent 2 — Books & Library
All files in `backend-django/books/` and `backend-django/library/`:
- Books: `models.py` (Book, BookAuthor, BookTag, BookGenre, AIExtractionStatus), `views.py` (BookListView, BookRetrieveView, BookContainsCharacterView), `serializers.py`, `lookups.py`, `urls.py`, `admin.py`
- Library: `models.py` (Author, Serie, Genre, Tag), `views.py`, `serializers.py`, `urls/*.py`
- Tests for both apps

### Agent 3 — Reviews & Signals
All files in `backend-django/reviews/`:
- `models.py` — Review model with unique_together(book, user)
- `signals.py` — post_save/post_delete signal updating Book.avg_rating
- `views.py` — ReviewListCreateView, BookReviewListCreateView, ReviewDetailView
- `serializers.py` — ScopedReviewCreateSerializer
- `tests/` — test_signals.py, test_views.py, test_book_scoped.py, test_edge_cases.py

### Agent 4 — Shelf & Collections
All files in `backend-django/shelf/`:
- `models.py` — ShelfEntry (unique_together user+book, clean() date validation), Shelf (unique_together user+slug), ShelfMembership (unique_together shelf+book)
- `views.py` — ShelfListView, ShelfEntryView, MyShelvesView, MyShelfDetailView, MyShelfBookView
- `serializers.py` — ShelfEntrySerializer, ShelfSerializer, ShelfDetailSerializer, ShelfCreateSerializer
- `tests/` — test_views.py, test_collections.py, test_edge_cases.py

### Agent 5 — Analysis & Entities
Application-layer files in `backend-django/analysis/`:
- `models.py` — BookCharacter (canonical FK self, source, confidence, is_hidden, slug), BookPlace, BookOrganization, CharacterRelationship (24 types, unique_together from+to+book)
- `views.py` — AIExtractionTriggerView, AIExtractionRetrieveView, BookCharacterHideView, BookCharacterMergeView
- `serializers.py` — BookCharacterSerializer, CharacterRelationSerializer, AIExtractionSerializer, MergeRequestSerializer
- `urls.py`
- `tests/test_models.py`, `tests/test_views.py`
- Exclude: `tasks.py`, `ner_engine.py`, `llm_engine.py`, `text_parser.py`, `text_stats.py` (NLP pipeline internals)

### Agent 6 — Frontend Auth & API
Files in `svelte-frontend/src/`:
- `hooks.server.ts` — cookie passthrough from browser to Django
- `lib/api/_client.ts` — base API client, fetch wrapper, error handling, 401 retry
- `lib/api/user.ts` — user-related API functions
- `lib/config.ts` — API base URL

### Agent 7 — Frontend UI & Routes
Files in `svelte-frontend/src/`:
- `routes/+layout.svelte` — root layout, auth state
- `routes/+page.svelte` — home page
- `routes/+page.server.ts` — server load function
- `app.html` — HTML shell
- `app.css` — global styles (Tailwind v4)
- `lib/utils.ts` — utility functions

### Agent 8 — API Contract
Cross-reference:
- Backend: all `urls.py` files across all apps + `config/urls.py`
- Frontend: `src/lib/types/api.generated.ts`, `src/lib/api/user.ts`
- Field mapping: verify snake_case (backend) to camelCase (frontend) conversion
- Check for: missing endpoints in generated types, endpoints called but not in generated types, field name mismatches

### Agent 9 — Architecture Critic
Reads all application code + all ADRs (`docs/decisions/ADR-*.md`). Generates two perspectives:
1. **Defense**: Why the current architecture is sound. Which decisions were correct. What trade-offs are justified.
2. **Counter**: What could be done differently. Which decisions have hidden costs. What alternatives exist and why they might be better.

### Agent 10 — Architect
Reads all application code. Reports:
- Dead code (unused imports, unused functions, unreachable paths)
- Bad patterns (god objects, circular dependencies, leaky abstractions)
- Good patterns (clean separation, well-designed APIs, consistent conventions)
- Structural observations (directory layout, module boundaries, naming consistency)

### Agent 11 — Overengineering Detector
Reads all application code. Reports:
- Premature abstractions (interfaces/extractions for single implementations)
- YAGNI violations (features built but not needed)
- Excessive indirection (extra layers that don't add value)
- Gold-plating (overly complex solutions for simple problems)

---

## Constraints

- No code changes — read-only audit
- Branch: `audit/full-backend-frontend-api` created from `main`
- All findings must reference `file:line`
- Severity must be consistent across agents (orchestrator unifies)
- Report saved to `docs/audits/2026-05-24-full-audit.md`

---

## Verification

After report generation, orchestrator runs:
1. `ruff check backend-django/` — baseline lint
2. `npm run check` in `svelte-frontend/` — baseline type check
3. `DJANGO_ENV=dev uv run python manage.py test` — baseline test results
4. `grep` for secrets in application code
5. Includes output of each in the Metrics section of the report
