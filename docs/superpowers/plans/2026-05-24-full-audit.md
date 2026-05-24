# Full Backend + Frontend + API Contract Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an independent, documentation-only audit report covering backend Django app logic, SvelteKit frontend, and API contract consistency.

**Architecture:** 11 subagents dispatched in 2 parallel phases. Phase 1: 8 inspection agents each review a scoped section of the codebase. Phase 2: 3 meta-analysis agents review the entire codebase from architectural, pattern, and overengineering perspectives. Phase 3: orchestrator collects all outputs, deduplicates, unifies severity, and writes the final report to `docs/audits/2026-05-24-full-audit.md`.

**Tech Stack:** Bash (git), Python/Django (ruff, pytest), Node/SvelteKit (npm), Markdown (report output)

**Spec:** `docs/superpowers/specs/2026-05-24-full-audit.md`

---

### Task 1: Prepare audit environment

**Files:**
- Create: `docs/audits/` (directory)
- Modify: none (working tree checkout)

- [ ] **Step 1: Create audit branch from main**

```bash
git fetch origin
git checkout main
git pull origin main
git checkout -b audit/full-backend-frontend-api
```

Expected: on new branch `audit/full-backend-frontend-api` based on latest `main`.

- [ ] **Step 2: Create audits directory**

```bash
mkdir -p docs/audits
```

- [ ] **Step 3: Run baseline backend lint**

```bash
uv run ruff check .
```
Workdir: `backend-django/`

Capture full output. Note any existing errors/warnings. These are pre-existing — do NOT fix them.

- [ ] **Step 4: Run baseline backend tests**

```bash
DJANGO_ENV=dev uv run python manage.py test --verbosity=2
```
Workdir: `backend-django/`

Capture full output. Record: total tests, passed, failed, skipped. Note any failures.

- [ ] **Step 5: Run baseline frontend check**

```bash
npm run check
```
Workdir: `svelte-frontend/`

Capture full output. Note any type errors.

- [ ] **Step 6: Run baseline frontend lint**

```bash
npm run lint
```
Workdir: `svelte-frontend/`

Capture full output. Note any warnings/errors.

- [ ] **Step 7: Commit baseline results**

```bash
git add docs/audits/
git commit -m "chore(audit): baseline environment setup"
```

---

### Task 2: Phase 1 — Dispatch inspection agents (1-8) in parallel

**Files:**
- None (read-only dispatch)

Dispatch ALL 8 agents in ONE message with 8 parallel `subtask` tool calls. Each agent gets its prompt from the spec. Wait for ALL to return before proceeding to Task 3.

- [ ] **Step 1: Dispatch Agent 1 (Auth & Users)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the Auth & Users Django app.

Read ALL of these files under /home/dv6/GitHub/storyshelf/backend-django/users/:
- cookie_auth.py, views.py, serializers.py, models.py, exporters.py
- urls/auth.py, urls/users.py, urls/public.py
- tests/ (all 12 test files)

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. JWTCookieAuthentication correctness — cookie read, header fallback, refresh flow, logout cookie clearing
2. Permission classes on views — IsAuthenticated vs AllowAny vs IsAdminUser — are they correct?
3. Serializer field validation — are all fields properly validated? Overly permissive?
4. GDPR export (exporters.py) — does it include all user data? Missing fields?
5. Account deletion — cascade or SET_NULL? Data leakage risk?
6. ADR-001 compliance — JWT access token NEVER stored in localStorage, refresh token path-restricted, CSRF protection
7. N+1 query potential — missing select_related/prefetch_related
8. Test coverage — what scenarios are tested? What's missing? Are tests actually testing behavior or just green-pass?
9. Avatar upload — file type validation, size limits, path traversal risk
10. UserFollow — self-follow prevention, duplicate prevention
11. Unique constraints — User.email, User.handle

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 2: Dispatch Agent 2 (Books & Library)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the Books & Library Django apps.

Read ALL files under:
- /home/dv6/GitHub/storyshelf/backend-django/books/ (models.py, views.py, serializers.py, lookups.py, urls.py, admin.py, tests/)
- /home/dv6/GitHub/storyshelf/backend-django/library/ (models.py, views.py, serializers.py, urls/*.py, admin.py, tests/)

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. Book model — AIExtractionStatus choices, slug uniqueness, avg_rating consistency, ratings_count accuracy, on_delete for FK fields
2. BookAuthor/BookTag/BookGenre — through models correctly defined? unique_together constraints?
3. BookListView — pagination, filters (genre, sort, search), n+1 queries (select_related for serie, prefetch for authors)
4. BookRetrieveView — slug routing (BookSlugLookup), deep serialization, characters relation
5. BookContainsCharacterView — query param validation, performance with large character sets
6. Serializer nested writes — Author/Genre/Tag creation via Book write? Overly permissive?
7. Library models — Author (bio), Serie (status choices), Genre/Tag — constraints, admin register
8. AuthorListView/RetrieveView — pagination, n+1
9. SerieListView/RetrieveView — status filter
10. Test coverage per app — which models/views/serializers tested? Gaps?
11. Book.text field — is this properly cleared after NLP? Cleanup in serializer vs model?
12. avg_rating signal — does it fire from reviews app correctly? Check integration

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 3: Dispatch Agent 3 (Reviews & Signals)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the Reviews app with special attention to Django signals.

Read ALL files under /home/dv6/GitHub/storyshelf/backend-django/reviews/:
- models.py, signals.py, views.py, serializers.py, urls.py
- tests/ (test_signals.py, test_views.py, test_book_scoped.py, test_edge_cases.py)

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. Review model — rating validation (1-5), content max_length, unique_together(book, user)
2. SIGNALS — post_save AND post_delete on Review:
   - Does avg_rating recalculate correctly after save? After delete?
   - Does ratings_count increment/decrement correctly?
   - Edge case: what happens when first review is created? Last review is deleted?
   - Does the signal use aggregate or manual math? Risk of race condition?
   - Is there a transaction safety issue?
3. ReviewListCreateView — pagination, user filter
4. BookReviewListCreateView — scoped to book, pre-fills book FK
5. ReviewDetailView — ownership check (can user Y edit user X's review?)
6. ScopedReviewCreateSerializer — does it prevent duplicate reviews per book?
7. Permission classes — can unauthenticated users read reviews? Create reviews?
8. Test coverage — do tests cover signal edge cases? Deletion recalculation? Concurrent review creation?
9. avg_rating precision — float rounding issues?

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 4: Dispatch Agent 4 (Shelf & Collections)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the Shelf & Collections app.

Read ALL files under /home/dv6/GitHub/storyshelf/backend-django/shelf/:
- models.py, views.py, serializers.py, urls.py
- tests/ (test_views.py, test_collections.py, test_edge_cases.py)

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. ShelfEntry model:
   - unique_together(user, book) enforced at DB level?
   - Status choices (want_to_read, reading, read) validated?
   - clean() method — start_date vs finish_date validation (must be finish >= start)
   - Is clean() actually called? Full_clean in view? Or only model.save which skips clean()?
   - personal_rating — same 1-5 as Review? Consistent?
2. Shelf model:
   - unique_together(user, slug) — enforced?
   - is_public default — correct?
   - Slug generation — auto or manual? Duplicate handling?
3. ShelfMembership model:
   - unique_together(shelf, book) — prevents duplicates
   - position field — ordering, gap handling
   - CASCADE on shelf delete?
4. ShelfListView — only shows books? Or shelves too? Correct permission?
5. ShelfEntryView — create/update/delete shelf entries? Ownership check?
6. MyShelvesView — shows user's own shelves
7. MyShelfDetailView — shows shelf contents with membership data
8. MyShelfBookView — add/remove books from shelves
9. Test coverage — is clean() validation tested? Edge cases with dates?
10. Pagination on list views
11. Permission classes — all shelf operations require authentication?

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 5: Dispatch Agent 5 (Analysis & Entities)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the Analysis & Entities app (application layer only, NOT NLP pipeline internals).

Read these files under /home/dv6/GitHub/storyshelf/backend-django/analysis/:
- models.py, views.py, serializers.py, urls.py
- tests/test_models.py, tests/test_views.py

DO NOT read: tasks.py, ner_engine.py, llm_engine.py, text_parser.py, text_stats.py

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. BookCharacter model:
   - unique_together(name, book) AND (slug, book) — both enforced?
   - source field (human/ai/ai-verified) — choices validated?
   - confidence field — 0-1 range? Validated?
   - is_hidden — soft-delete mechanism. Does filtering exclude hidden by default?
   - canonical FK (self) — what's the merge flow? Unmerged chars point to canonical. Is cycle detection needed?
   - slug — auto-generated? Collision handling?
2. BookPlace model — unique_together(name, book), mention_count
3. BookOrganization model — same checks as BookPlace
4. CharacterRelationship model:
   - 24 relation types — all valid? Choices enum?
   - unique_together(from, to, book)
   - Symmetry: if A is "ally" of B, should B's relationship be set too? Or is it directional?
5. AIExtractionTriggerView — admin-gated (IsAdminUser)? POST only? Idempotent?
6. AIExtractionRetrieveView — returns extraction status
7. BookCharacterHideView — soft-delete (sets is_hidden). Admin only? Reversible?
8. BookCharacterMergeView — merges characters via canonical FK. Validation? What happens to relationships of merged characters?
9. Test coverage — model constraints tested? Merge logic tested? Hide/show tested?
10. ADR-002 compliance — are entities per-book (not global)? Check unique_together uses book FK
11. ADR-003 compliance — entity per-book design confirmed

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 6: Dispatch Agent 6 (Frontend Auth & API)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the SvelteKit frontend auth and API layer.

Read these files under /home/dv6/GitHub/storyshelf/svelte-frontend/src/:
- hooks.server.ts
- lib/api/_client.ts
- lib/api/user.ts
- lib/config.ts

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. hooks.server.ts:
   - Cookie forwarding — is the browser's cookie header forwarded to the Django API via event.fetch?
   - Is credentials: 'include' set on all fetches?
   - What happens when the Django API returns 401? Does hooks.server handle silent refresh?
   - Is there an infinite redirect loop risk? (e.g. 401 → /login → 401 → /login)
   - Base URL — hardcoded or from config? Does it handle dev vs prod?
   - Request URL construction — relative paths vs absolute? Any path traversal risk?
2. _client.ts:
   - Fetch wrapper — does it add any auth headers? (Should NOT — cookies handle auth)
   - Error handling — what response codes are handled? What's thrown/rejected?
   - 401 handling — does it attempt token refresh? Redirect to login?
   - Request/response interceptors — any transformations?
   - Timeout handling?
   - Base URL construction — from config or hardcoded?
3. user.ts:
   - API functions — do they match backend endpoints exactly?
   - Response type assertions — are they typed correctly from api.generated.ts?
   - Input validation before sending? Zod schemas?
   - Error handling per function
4. config.ts:
   - PUBLIC_API_BASE_URL — correct for dev (localhost:8000) and prod?
   - Any secrets or tokens in config? (Should be NONE — cookies handle auth)
   - Environment variable fallbacks?
5. ADR-001 compliance:
   - No localStorage/sessionStorage token storage
   - No manual Authorization header addition
   - Cookie passthrough is the sole auth mechanism
   - Refresh is handled by backend, not frontend JS

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 7: Dispatch Agent 7 (Frontend UI & Routes)**

Subtask prompt:

```
You are an audit agent. Your role: INSPECTION. Audit the SvelteKit frontend UI and routes.

Read these files under /home/dv6/GitHub/storyshelf/svelte-frontend/src/:
- routes/+layout.svelte
- routes/+page.svelte
- routes/+page.server.ts
- app.html
- app.css
- lib/utils.ts

Also read:
- /home/dv6/GitHub/storyshelf/svelte-frontend/svelte.config.js
- /home/dv6/GitHub/storyshelf/svelte-frontend/vite.config.ts
- /home/dv6/GitHub/storyshelf/svelte-frontend/tsconfig.json

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. +layout.svelte:
   - Auth state handling — is user state passed from server to client?
   - Loading/error/empty states — what shows while auth is initializing?
   - Flash of unauthenticated content? (auth check must complete before rendering protected UI)
   - Dark mode handling — mode-watcher integration
2. +page.svelte:
   - Home page content — what's shown for unauthenticated vs authenticated?
   - Error boundaries — if server load fails, what's displayed?
3. +page.server.ts:
   - Load function — what data is fetched? Error handling?
   - Auth required? Or public page?
4. app.html:
   - Meta tags — viewport, charset, description
   - Any inline scripts that could access cookies?
   - CSP headers?
5. app.css:
   - Tailwind v4 imports — correct setup?
   - Custom CSS besides Tailwind?
6. lib/utils.ts:
   - Purpose of each exported function
   - Browser-only vs server-safe?
7. Build config:
   - svelte.config.js — adapter-node? Correctly configured?
   - vite.config.ts — Tailwind plugin, resolve aliases, dev port
   - tsconfig.json — strict mode? Path aliases?
8. ADR-004 compliance:
   - No Vue 3 code or references remaining (ADR says hard remove done in 2.6)
   - Check if any `import from 'vue'` or `.vue` file references exist

Return: numbered list of findings grouped by severity (Critical/High/Medium/Low). Each finding MUST have file:line.
```

- [ ] **Step 8: Dispatch Agent 8 (API Contract)**

Subtask prompt:

```
You are an audit agent. Your role: API CONTRACT CROSS-REFERENCE. Verify backend API against frontend types.

Read ALL URL configuration files:
- /home/dv6/GitHub/storyshelf/backend-django/config/urls.py
- /home/dv6/GitHub/storyshelf/backend-django/users/urls/auth.py
- /home/dv6/GitHub/storyshelf/backend-django/users/urls/users.py
- /home/dv6/GitHub/storyshelf/backend-django/users/urls/public.py
- /home/dv6/GitHub/storyshelf/backend-django/books/urls.py
- /home/dv6/GitHub/storyshelf/backend-django/library/urls/authors.py
- /home/dv6/GitHub/storyshelf/backend-django/library/urls/series.py
- /home/dv6/GitHub/storyshelf/backend-django/library/urls/genres.py
- /home/dv6/GitHub/storyshelf/backend-django/reviews/urls.py
- /home/dv6/GitHub/storyshelf/backend-django/shelf/urls.py
- /home/dv6/GitHub/storyshelf/backend-django/analysis/urls.py

Read frontend files:
- /home/dv6/GitHub/storyshelf/svelte-frontend/src/lib/types/api.generated.ts
- /home/dv6/GitHub/storyshelf/svelte-frontend/src/lib/api/user.ts

For each finding, report: [severity] file:line — description — recommendation

Check for:
1. Extract EVERY API endpoint from backend url files as: METHOD PATH (e.g., GET /api/books/, POST /api/auth/register/)
2. For each endpoint, check if it exists in api.generated.ts — if missing, report as gap
3. For each function in user.ts, verify:
   - Does it call an existing backend endpoint?
   - Does the HTTP method match?
   - Does the request body shape match the backend serializer?
   - Does the response type from api.generated.ts match what the backend returns?
4. Snake_case → camelCase conversion:
   - Backend serializers use snake_case (Python convention)
   - Frontend types from OpenAPI codegen — are they camelCase? snake_case? Mixed?
   - Is there a transformation layer? Or does the OpenAPI schema already map?
   - If no mapping exists, frontend will send/receive snake_case OR fail silently
5. Pagination format:
   - DRF default: { count, next, previous, results }
   - Does api.generated.ts expect this shape? Or flat array?
   - Mismatch here = frontend .map() on undefined
6. Auth-required endpoints:
   - Which backend endpoints require authentication?
   - Does frontend call them without proper auth setup?
7. Path parameters:
   - Backend: /api/books/{slug}/  — does frontend use slug or id?
   - Any URL construction that hardcodes IDs when backend expects slugs?
8. Missing frontend coverage:
   - Backend endpoints with NO frontend call at all (unused/dead API?)
   - Frontend functions calling endpoints not in url files (phantom calls?)

Return:
- Table: METHOD | Backend Path | api.generated.ts (yes/no) | user.ts function | Status (OK/Mismatch/Missing)
- Numbered list of findings grouped by severity
- Each finding MUST have file:line
```

- [ ] **Step 9: Verify all 8 agents returned**

Confirm all 8 subagents have completed and returned their findings. Collect all outputs into a working buffer.

If any agent failed or returned incomplete results, re-dispatch that specific agent with refined prompt.

---

### Task 3: Phase 2 — Dispatch meta-analysis agents (9-11) in parallel

**Files:**
- None (read-only dispatch)

Dispatch ALL 3 agents in ONE message with 3 parallel `subtask` tool calls. Wait for ALL to return before proceeding to Task 4.

- [ ] **Step 1: Dispatch Agent 9 (Architecture Critic — 2 perspectives)**

Subtask prompt:

```
You are an audit agent. Your role: ARCHITECTURE CRITIC. Provide TWO independent perspectives on the StoryShelf architecture.

Read the architecture documentation:
- /home/dv6/GitHub/storyshelf/docs/ARCHITECTURE.md
- /home/dv6/GitHub/storyshelf/docs/decisions/ADR-001-jwt-httponly-cookies.md
- /home/dv6/GitHub/storyshelf/docs/decisions/ADR-002-dwa-workery-celery.md
- /home/dv6/GitHub/storyshelf/docs/decisions/ADR-003-encje-ner-per-book.md
- /home/dv6/GitHub/storyshelf/docs/decisions/ADR-004-vue-removal.md

Read the application code (models, views, serializers) across ALL Django apps:
- /home/dv6/GitHub/storyshelf/backend-django/books/
- /home/dv6/GitHub/storyshelf/backend-django/library/
- /home/dv6/GitHub/storyshelf/backend-django/users/
- /home/dv6/GitHub/storyshelf/backend-django/shelf/
- /home/dv6/GitHub/storyshelf/backend-django/reviews/
- /home/dv6/GitHub/storyshelf/backend-django/analysis/
- /home/dv6/GitHub/storyshelf/svelte-frontend/src/

Provide TWO clearly separated perspectives:

PERSPECTIVE 1 — Defense of Current Architecture:
- Why the current architecture is sound
- Which decisions were correct and well-justified
- What trade-offs are justified given the project's scale and goals (hobby/portfolio, single-tenant, <10k books)
- What the architecture does well
- Where the ADRs hold up under scrutiny

PERSPECTIVE 2 — Counter-arguments & Alternatives:
- What could be done differently
- Which decisions have hidden costs or future pain points
- What alternatives exist and why they might be better
- What would break at 10x scale
- Where the ADRs are weakest or most debatable
- What a "v2 rewrite" would change and why

For each perspective, be specific: reference files, code patterns, and concrete examples. Don't be vague.
```

- [ ] **Step 2: Dispatch Agent 10 (Architect — patterns, dead code, structure)**

Subtask prompt:

```
You are an audit agent. Your role: ARCHITECT. Review the codebase for dead code, pattern quality, and structural coherence.

Read ALL application files:
- All .py files under /home/dv6/GitHub/storyshelf/backend-django/ (exclude migrations/, __pycache__/, .venv/)
- All .svelte and .ts files under /home/dv6/GitHub/storyshelf/svelte-frontend/src/

Report on:

1. DEAD CODE:
   - Unused imports (import X but X never referenced)
   - Unused functions/methods (defined but never called within the codebase)
   - Unused classes (defined but never instantiated or extended)
   - Commented-out code blocks
   - Unreachable code paths (if False, return after raise, etc.)
   - Variables assigned but never read
   - Empty or stub files (only pass, only return None, empty class bodies)

2. BAD PATTERNS:
   - God objects/views (files >300 lines doing too many things)
   - Circular dependencies between apps (import loops)
   - Leaky abstractions (internal details exposed unnecessarily)
   - Inconsistent error handling (some places try/except, others don't)
   - Hardcoded strings that should be constants/enums
   - Magic numbers
   - Duplicated logic across apps (copy-paste code)
   - Models with business logic (fat models pattern vs service layer)

3. GOOD PATTERNS (acknowledge what's done well):
   - Clean separation of concerns
   - Consistent naming conventions
   - Well-designed API surfaces
   - Proper use of Django/DRF/SvelteKit conventions
   - Good error handling patterns

4. STRUCTURAL OBSERVATIONS:
   - Directory layout — logical grouping? Flat vs nested?
   - Module boundaries — are app boundaries clear? Cross-app coupling?
   - Naming consistency — same concept named differently across files?
   - Import patterns — relative vs absolute, star imports
   - Test file organization — mirror source structure?

Return: three sections (Dead Code, Patterns, Structure) with numbered findings. Each with file:line.
```

- [ ] **Step 3: Dispatch Agent 11 (Overengineering Detector)**

Subtask prompt:

```
You are an audit agent. Your role: OVERENGINEERING DETECTOR. Find places where the code is more complex than the problem warrants.

Read ALL application files:
- All .py files under /home/dv6/GitHub/storyshelf/backend-django/ (exclude migrations/, __pycache__/, .venv/)
- All .svelte and .ts files under /home/dv6/GitHub/storyshelf/svelte-frontend/src/

Look for:

1. PREMATURE ABSTRACTIONS:
   - Base classes / mixins with only ONE subclass/user
   - Abstract interfaces defined before concrete needs
   - Factory patterns for single implementations
   - Strategy patterns where only one strategy exists
   - Generic utilities that handle "future use cases" never realized
   - Config/constants files with unused values

2. YAGNI VIOLATIONS:
   - Features built but not in spec/roadmap (gold-plating)
   - Fields on models that are never read/written
   - Serializer fields that are always excluded or never populated
   - API endpoints with no consumers
   - Validation rules for scenarios that can't happen
   - Admin customizations for models rarely/never edited in admin

3. EXCESSIVE INDIRECTION:
   - Wrapper functions that just call another function with same signature
   - Layers of abstraction that don't add value (X → XService → XManager → X)
   - Helper files where helpers are only used once
   - URL configurations split into too many files for simple apps
   - Serializers separated from views with no reuse

4. COMPLEXITY FOR COMPLEXITY'S SAKE:
   - Overly clever Python metaprogramming where simple code would work
   - Custom class-based views where function views would suffice
   - Complex queryset annotations that could be simple filters
   - Nested serializers when flat would work
   - Async patterns in synchronous Django (Django 6 is sync by default)
   - Custom middleware/decorators that duplicate Django built-ins
   - Custom pagination class that replicates DRF defaults

5. SCALE MISMATCH:
   - Patterns appropriate for 1M users applied to a single-tenant hobby project
   - Enterprise patterns (CQRS, event sourcing, saga) for CRUD operations
   - Microservice patterns in a monolith

For each finding: [severity] file:line — what's overengineered — simpler alternative

Return: numbered list grouped by category. Each finding MUST have file:line.
```

- [ ] **Step 4: Verify all 3 meta-analysis agents returned**

Confirm all 3 subagents have completed. Collect outputs.

---

### Task 4: Orchestrate — assemble final report

**Files:**
- Create: `docs/audits/2026-05-24-full-audit.md`

- [ ] **Step 1: Collect all agent outputs**

Combine findings from all 11 agents into one working buffer. Group by severity (Critical → High → Medium → Low).

- [ ] **Step 2: Deduplicate findings**

Check for overlapping findings across agents. If two agents found the same issue:
- Keep the one with more detail or better file:line reference
- Merge if they provide complementary information
- Note in report: "Also flagged by Agent X"

- [ ] **Step 3: Unify severity across agents**

Agents may interpret severity differently. Re-evaluate each finding against the official scale:
- Critical: deployment-blocker, security, data loss
- High: architectural flaw, missing error handling, API mismatch causing runtime errors
- Medium: missing tests, N+1 query, minor ADR deviation
- Low: style, naming, dead imports

- [ ] **Step 4: Generate metrics section**

Compute from agent outputs and baseline data:
- Total Python files, test files, test pass/fail counts
- Total Svelte files, TypeScript files
- Endpoints in backend url files: count
- Endpoints with missing frontend types: count
- Endpoints with no frontend consumer: count
- Dead code instances found: count
- Overengineering instances found: count
- Pre-existing lint errors (from baseline): count
- Pre-existing test failures (from baseline): count

- [ ] **Step 5: Write the report**

Use the template from the spec:

```markdown
# StoryShelf Independent Audit — 2026-05-24

## 1. Executive Summary
[2-3 paragraphs: overall state, critical issues count, key recommendations]

## 2. Critical Issues
[Table: # | Severity | Agent | File:Line | Description | Recommendation]

## 3. High Issues
[Same table format]

## 4. Medium Issues
[Same table format]

## 5. Low Issues
[Same table format]

## 6. API Contract Matrix
| Method | Backend Path | Frontend Type (api.generated.ts) | Frontend Call (user.ts) | Status |
|--------|-------------|----------------------------------|------------------------|--------|

## 7. ADR Compliance
| ADR | Decision | Code Compliance | Evidence File:Line | Notes |

## 8. Architecture Critique
### Perspective 1 — Defense of Current Architecture
[Agent 9 output, Perspective 1]

### Perspective 2 — Counter-arguments & Alternatives
[Agent 9 output, Perspective 2]

## 9. Architect's Notes
### Dead Code
[Agent 10 output]
### Pattern Quality
[Agent 10 output]
### Structural Observations
[Agent 10 output]

## 10. Overengineering Report
[Agent 11 output]

## 11. Metrics
- Backend: N Python files | N test files | N tests (N passed, N failed, N skipped)
- Frontend: N Svelte files | N TS files
- Backend endpoints: N
- Endpoints with no frontend type: N
- Endpoints with no frontend consumer: N
- Dead code instances: N
- Overengineering instances: N
- Pre-existing lint errors: N
- Pre-existing test failures: N

## 12. Priority Recommendations
1. [Most impactful first, with reasoning]
2. ...
```

- [ ] **Step 6: Commit report**

```bash
git add docs/audits/2026-05-24-full-audit.md
git commit -m "docs(audit): full independent audit report — backend, frontend, API contract"
```

---

### Task 5: Final verification

**Files:**
- Read: `docs/audits/2026-05-24-full-audit.md`

- [ ] **Step 1: Run same baselines as Task 1 for comparison**

```bash
uv run ruff check .
```
Workdir: `backend-django/`

Confirm no NEW errors introduced (output should be identical to baseline).

```bash
DJANGO_ENV=dev uv run python manage.py test --verbosity=2 2>&1 | tail -5
```
Workdir: `backend-django/`

Confirm test results unchanged from baseline.

```bash
npm run check 2>&1
```
Workdir: `svelte-frontend/`

```bash
npm run lint 2>&1
```
Workdir: `svelte-frontend/`

- [ ] **Step 2: Verify report completeness**

Check the report has all 12 sections. No section should be empty or marked "TODO".

- [ ] **Step 3: Commit final verification**

```bash
git add -A
git diff --cached --stat
git commit -m "chore(audit): final verification — baseline unchanged"
```

---

### Summary

| Task | Description | Agents | Files Created |
|------|-------------|--------|---------------|
| 1 | Prepare environment | — | `docs/audits/` |
| 2 | Phase 1: Inspection (8 agents) | 8 parallel subtasks | — |
| 3 | Phase 2: Meta-analysis (3 agents) | 3 parallel subtasks | — |
| 4 | Orchestrate into report | — | `docs/audits/2026-05-24-full-audit.md` |
| 5 | Final verification | — | — |

**Total: 11 subagents, 1 report**

**No code files modified. Read-only audit.**
