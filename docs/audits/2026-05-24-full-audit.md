# StoryShelf Independent Audit — 2026-05-24

## 1. Executive Summary

StoryShelf is a hobby/portfolio Django+SvelteKit monolith for book tracking with NLP-powered entity extraction. The audit covered 6 Django backend apps, SvelteKit frontend, API contract consistency, architecture critique, dead code detection, and overengineering analysis across 12 subagents.

**Overall state: solid.** The codebase is clean, well-structured, and follows Django/DRF conventions consistently. ADR decisions are well-justified. The NLP pipeline design (ADR-003 — simplified from 5 tasks to 2) is a rare example of deliberate de-engineering.

**3 critical issues found:**
1. Race condition in `reviews/signals.py` — `Book.avg_rating` non-atomic read-modify-write under concurrent requests
2. No default `is_hidden` filtering on `BookCharacter` — soft-deleted characters leak to API consumers
3. Missing 401→refresh→retry loop in frontend `_client.ts` — expired access tokens cause hard failures instead of transparent renewal

**Key recommendation:** Fix the 3 criticals before production use. Then address the 2 active bugs (`Review.__str__` crash, admin `user__username` search), adopt a consistent camelCase convention across all serializers, and add pagination to currently unlimited list endpoints. The architecture scales well for <10k books; the main scalability concern is the `avg_rating` signal pattern under bulk operations.

---

## 2. Critical Issues

| # | App | Agent | File:Line | Description | Recommendation |
|---|-----|-------|-----------|-------------|----------------|
| 1 | reviews | 4 | `reviews/signals.py:13-18` | **Race condition on avg_rating**: signal performs non-atomic `aggregate()` then `update()`. Two concurrent requests can interleave read and write, producing permanently wrong count/average. | Wrap in `transaction.atomic()` with `select_for_update()` on Book row, or use `F()`-expression-based update. |
| 2 | analysis | 6 | `analysis/models.py:37` (+ serializers) | **No default `is_hidden` filter**: `BookCharacter.is_hidden` soft-delete has no custom manager or default queryset. All consumers except `get_confidence_summary()` return hidden characters. Hidden data leaks via extraction API. | Add custom manager with `visible()` method or override default queryset to exclude `is_hidden=True`, with explicit `.all_with_hidden()` for admin. |
| 3 | frontend | 7 | `svelte-frontend/src/lib/api/_client.ts:24-32` | **Missing 401 auto-retry (token refresh)**: ADR-001 specifies transparent refresh via 401 → POST `/api/users/token/refresh/` → retry. Client treats 401 same as any error — no retry. Access token expiry (15 min) causes hard failures. | Implement 401 interceptor: detect 401 → POST `/auth/refresh/` (with `credentials: 'include'`) → retry original request ×1. |

## 3. High Issues

| # | App | Agent | File:Line | Description | Recommendation |
|---|-----|-------|-----------|-------------|----------------|
| 4 | users | 1a | `users/models.py:32` | **Profile public by default**: `profile_public` defaults to `True` — new accounts are immediately public. GDPR principle of data minimization suggests opt-in. | Change to `default=False`. |
| 5 | users | 1a | `users/exporters.py:66-71` | **GDPR export missing timestamps/IDs**: `follows.json` omits `followed_at` timestamp and `UserFollow.id`, reducing audit trail completeness. | Include `followed_at` and follow ID. |
| 6 | books | 2 | `books/views.py:83-84` | **Double query in BookRetrieveView**: `resolve_book()` fires `get_object_or_404` (query 1), then `qs.get(pk=book.pk)` fires another query with prefetches. First query wasted. | Merge into single query with prefetches on the initial lookup. |
| 7 | books | 2 | `books/serializers.py:108` | **Prefetch-bypassing `.exists()`**: `instance.characters.filter(is_hidden=False).exists()` hits DB despite Prefetch cache set up in view. N+1 per detail request. | Use `any()` over cached queryset, or check `is_hidden`/`canonical` in Python. |
| 8 | books | 2 | `books/models.py:18-20,59-62` | **TOCTOU race in slug generation**: `while Book.objects.filter(slug=slug).exists()` + `self.slug = slug` is not atomic. Concurrent saves of identically-titled books can produce duplicates → 500. | Wrap in `transaction.atomic()` with retry, or use DB-level approach. |
| 9 | shelf | 5 | `shelf/serializers.py:8-14` vs `shelf/views.py:80-81` | **Serializer/PATCH field mismatch**: PATCH accepts `start_date`/`finish_date`/`personal_rating` but serializer doesn't expose them. After PATCH, response lacks the just-set values. Frontend blind to date state. | Add fields to `ShelfEntrySerializer`. |
| 10 | shelf | 5 | `shelf/views.py:61` | **`get_or_create` bypasses `model.clean()`**: POST uses `get_or_create` → `save()` without `full_clean()`. Date cross-validation in `clean()` never runs on create. | Call `entry.full_clean()` after `get_or_create`. |
| 11 | analysis | 6 | `analysis/models.py:115-162` | **Relationship asymmetry undocumented**: Purely directional (A→B). Symmetric types (`spouse_of`, `sibling_of`, `friend_of`) don't auto-create reciprocal rows. Querying "who is B's spouse?" returns nothing. | Document as intentional directional design, or add optional reciprocal creation for symmetric types. |
| 12 | analysis | 6 | `books/urls.py:15-18` vs `analysis/urls.py:1-12` | **MergeView routed under books/ but defined in analysis/**: Scatters character management across two URL modules. | Move merge and hide routes to `analysis/urls.py`. |
| 13 | library | 3 | `library/models.py:43` etc. | **Tag model has no API exposure**: Defined in models, registered in admin, but no serializer, no view, no URL endpoint. | Add Tag API endpoints or document as admin-only. |
| 14 | frontend-ui | 8 | `svelte-frontend/src/routes/` | **No `+layout.server.ts`**: Auth state not loaded at layout level. Every page calls `getCurrentUser()` independently → N+1 API calls per navigation, flash of unauthenticated content. | Add `+layout.server.ts` that loads user once, pass via `$props()`, show spinner while loading. |
| 15 | frontend-ui | 8 | `svelte-frontend/src/routes/` | **No `+error.svelte`**: No custom error boundary. Server load failures show generic SvelteKit internal error page. | Create `+error.svelte` with Tailwind styling. |
| 16 | api-contract | 9 | `books/serializers.py:135`, `api.generated.ts:1198` | **BookDetail response shape not modeled**: Backend returns `{book, shelfEntry, characters, relations}` but generated type `BookDetail` only models inner book object. `shelfEntry`/`characters`/`relations` would type-check as undefined. | Add `BookDetailResponse` schema to OpenAPI or use `@extend_schema` to document real shape. |
| 17 | api-contract | 9 | `api.generated.ts:1950-2093` | **All `/api/users/me/*` endpoints have `content?: never`**: `drf-spectacular` not picking up serializer schemas for `APIView`-based views (uses `generics.*` auto-generation only). | Add `@extend_schema(responses={200: ...})` decorators to UserMeView, PasswordChangeView, etc. |
| 18 | api-contract | 9 | Multiple | **snake_case/camelCase inconsistency**: `BookList.ratings_count` (snake) vs `BookDetail.ratingsCount` (camel) — same field, different names. `CharacterRelationSerializer` mixed in same object. | Pick camelCase for JSON API surface, normalize all serializers. |
| 19 | architect | 10 | `reviews/admin.py:10`, `shelf/admin.py:17` | **Admin search uses nonexistent `user__username`**: User model has `handle` not `username`. Admin search silently returns nothing. Also `Review.__str__` crashes with `AttributeError` on `self.user.username`. | Fix to `user__handle` and `self.user.handle`. |
| 20 | architect | 10 | `books/models.py:38` | **`Book.text` in main table**: Every `SELECT *` on Book (list views, admin) loads full text from DB. `BookListView` doesn't `.defer("text")`. Text cleared post-NLP but present until then. | Add `.defer("text")` to all list querysets; consider separate `BookContent` table long-term. |
| 21 | overengineer | 11 | `analysis/models.py:81-112` | **`BookPlace` and `BookOrganization` models dead**: NER-populated, zero API exposure, never read by any endpoint. | Remove or expose via API. |

## 4. Medium Issues

| # | App | Agent | File:Line | Description | Recommendation |
|---|-----|-------|-----------|-------------|----------------|
| 22 | users | 1a | `users/models.py:31` | Avatar no model-level file validation — only serializer. | Add `FileExtensionValidator` on model field. |
| 23 | users | 1a | `users/serializers.py:173-181` | FollowSerializer N+1 via `source=` lookups (follower.handle, following.handle). | Document view must `.select_related("follower","following")`. |
| 24 | users | 1a | `users/exporters.py:18-25` | GDP export `user.json` missing `id` and `is_active`. | Include both for GDPR data portability. |
| 25 | users | 1a | `users/serializers.py:92-93` | `get_settings()` fakes `settings` object from single boolean — misleading abstraction. | Add real `settings = JSONField` or rename key to `profile_public` directly. |
| 26 | users | 1b | `users/cookie_auth.py:16-18` | JWTCookieAuthentication drops Authorization header fallback — ADR-001 says it should be accepted. | Add header fallback after cookie check. |
| 27 | users | 1b | `users/views.py:260-269` | UserSettingsView has no GET — users can't read current settings value. | Add GET handler. |
| 28 | reviews | 4 | `reviews/views.py:20` | ReviewListCreateView disables pagination — unbounded query for flat review list. | Re-enable `StandardPagination`. |
| 29 | reviews | 4 | `reviews/tests/` | Missing tests: signal on review update (rating change), partial delete count recalculation. | Add tests for both paths. |
| 30 | reviews | 4 | `reviews/views.py:11-97` | Code duplication between ReviewListCreateView and BookReviewListCreateView (identical IntegrityError handling, permission logic). | Extract to shared mixin or base class. |
| 31 | books | 2 | `books/views.py:29-31` → `serializers.py:37-38` | N+1 when search joins invalidate author prefetch — `q` param triggers `bookauthor__author__name__icontains` which can bypass `prefetch_related`. | Use `prefetch_related(Prefetch("authors", to_attr="_prefetched_authors"))`. |
| 32 | books | 2 | `books/views.py:96` + `analysis/models.py:25` | Missing GIN trigram index on `BookCharacter.name` for `BookContainsCharacterView` `icontains` query. | `CREATE INDEX ... ON analysis_bookcharacter USING gin (name gin_trgm_ops)`. |
| 33 | books | 2 | `books/models.py:38` | `Book.text` retained indefinitely after extraction — data retention risk. | Clear text field after `AIExtractionStatus == DONE`. |
| 34 | books | 2 | `books/views.py:24` | `select_related("serie")` in BookListView but BookListSerializer never touches `serie`. | Remove or use only when needed. |
| 35 | shelf | 5 | `shelf/views.py:18`, `shelf/urls.py:13` | ShelfListView naming misleading — lists ShelfEntry objects not Shelf objects. | Rename to ShelfEntryListView. |
| 36 | shelf | 5 | `shelf/views.py:26,97` | No pagination on ShelfListView or MyShelvesView. | Add pagination or document intentional flat-list decision. |
| 37 | shelf | 5 | `shelf/views.py:80` | ShelfEntryView.patch doesn't update `personal_rating` — silently ignored. | Add to PATCH handler. |
| 38 | analysis | 6 | `analysis/tests/` | No tests for BookPlace or BookOrganization models (UniqueConstraint, FK cascade, mention_count). | Add `TestBookPlace` and `TestBookOrganization`. |
| 39 | analysis | 6 | `analysis/tests/test_models.py` | No source choices validation test, no confidence bounds test. | Add tests for invalid source and out-of-range confidence. |
| 40 | analysis | 6 | `analysis/serializers.py:62-66` | `covered_through` hardcoded stub (`chapter: null` always). | Implement or remove with TODO comment. |
| 41 | library | 3 | `library/views.py:27-33` | No status filter on SeriesListView. | Add `filter_backends` with status query param. |
| 42 | library | 3 | `library/tests/` | Missing Serie/Genre model uniqueness tests, serializer unit tests, method restriction tests. | Add tests. |
| 43 | frontend-api | 7 | `svelte-frontend/src/hooks.server.ts:5` | Imprecise cookie forwarding trigger — `includes('/api/')` matches any URL containing that substring. | Match against known API base URL. |
| 44 | frontend-api | 7 | `svelte-frontend/src/lib/api/_client.ts:15-21` | Options spread order makes `credentials` overridable and `headers` non-merging. | Move `...options` first, merge headers after. |
| 45 | frontend-api | 7 | `svelte-frontend/src/lib/api/_client.ts` | No request timeout — hung backend blocks SSR render indefinitely. | Add `AbortController` with 10s server-side timeout. |
| 46 | frontend-api | 7 | `svelte-frontend/src/lib/api/user.ts:3-12` | Manually typed `UserMe` interface — no generated types exist, drift risk. | Fix finding #17 first (OpenAPI schema), then regenerate types. |
| 47 | frontend-ui | 8 | `svelte-frontend/src/+page.server.ts:5-6` | API error silently maps to `user=null` — indistinguishable from "not logged in". | Return `{ user, error }` and render error banner in page. |
| 48 | frontend-ui | 8 | `svelte-frontend/src/lib/utils.ts:13-20` | `formatDate` uses `toLocaleDateString` with `en-GB` — can mismatch between SSR and client ICU data. | Use fixed formatter or `date-fns`. |
| 49 | api-contract | 9 | `svelte-frontend/src/lib/api/` | No API modules for books, shelf, reviews, library — only `user.ts` exists. All non-user endpoints unreachable from frontend. | Create API modules as next implementation step. |
| 50 | overengineer | 11 | `analysis/serializers.py:6` & `books/serializers.py:8` | Duplicate `BookCharacterSerializer` in two files — same model, different fields. | Consolidate to one location. |
| 51 | overengineer | 11 | `analysis/text_parser.py:31-42`, `text_stats.py:22-36` | `split_into_chapters()` and `analyse_text()` — defined and tested, zero application callers. Dead code. | Remove. |
| 52 | overengineer | 11 | `shelf/models.py:31-32` | `personal_rating` field with validators never exposed via serializer. | Remove or add to serializer. |
| 53 | overengineer | 11 | `config/settings/base.py:137-148` + config/celery.py | Celery+RabbitMQ+Redis for 2 async tasks — infrastructure overhead for hobby project. | Use `threading.Thread` or `django-rq` with Redis only. |

## 5. Low Issues

| # | App | Agent | File:Line | Description | Recommendation |
|---|-----|-------|-----------|-------------|----------------|
| 54 | users | 1a | `users/serializers.py:125` | `UserSettingsPatchSerializer.profile_public` lacks `required=False` — partial PATCH impossible if more fields added. | Add `required=False`. |
| 55 | users | 1a | `users/serializers.py:181` | `read_only_fields = fields` no-op — all fields already individually `read_only=True`. | Remove. |
| 56 | users | 1a | `users/exporters.py:26 vs 46,63` | Inconsistent `cls=_DatetimeEncoder` usage across export functions. | Normalize. |
| 57 | users | 1b | `users/cookie_auth.py:38-59` | `os.getenv` for JWT lifetimes instead of Django settings — inconsistent with other cookie config. | Use settings. |
| 58 | users | 1b | `users/views.py:250-254` | AvatarUpload deletes old file before saving new — brief gap with no avatar if save fails. | Save first, delete old after. |
| 59 | reviews | 4 | `reviews/models.py:16` | No `blank=False` on content field at model level — direct ORM calls can create empty reviews. | Add `blank=False` or `MinLengthValidator`. |
| 60 | reviews | 4 | `reviews/signals.py:18` | `round(avg, 2)` banker's rounding — negligible practical impact. | Low priority. Use Decimal if precision ever matters. |
| 61 | books | 2 | `books/views.py:59`, `serializers.py:106` | Redundant `is_admin` computation in both view and serializer. | Pass via serializer context. |
| 62 | books | 2 | `books/serializers.py:124-127` vs `views.py:61-64` | Duplicated character visibility filtering — view-side Prefetch + serializer-side filter re-query. | Drop serializer-side filter, use cached results. |
| 63 | books | 2 | `books/models.py:87 vs 54` | Confusing `related_name="book_genres"` on BookGenre through model (returns through instances, not Genre objects). | Rename to `book_genre_through`. |
| 64 | shelf | 5 | `shelf/models.py:31-33` | `personal_rating` validators only run during `full_clean()` — bypassed by direct `.save()`. | Override `save()` or document as API-only. |
| 65 | shelf | 5 | `shelf/models.py:97` | `ShelfMembership.position` defaults to 0 with no auto-management. | Auto-increment in `save()`. |
| 66 | shelf | 5 | `shelf/serializers.py:22` | Redundant `is_public = BooleanField()` — same as default ModelSerializer mapping. | Remove. |
| 67 | analysis | 6 | `analysis/models.py:48-51` | ADR-003 uses `unique_together` terminology; code uses `UniqueConstraint`. | Terminology mismatch — no action needed. |
| 68 | frontend-api | 7 | `svelte-frontend/src/lib/api/_client.ts:35-36` | 204 handling returns `data: null` — ambiguous with 200 empty body. | Add `status` to return value. |
| 69 | frontend-api | 7 | `svelte-frontend/src/lib/api/user.ts:14` | `getCurrentUser` hardcodes `isServerSide = true` — misleading API. | Rename or remove parameter. |
| 70 | frontend-api | 7 | `svelte-frontend/src/lib/config.ts:4` | `PUBLIC_API` appears dead — never imported or used. | Remove or add comment. |
| 71 | frontend-api | 7 | `svelte-frontend/src/lib/api/_client.ts:41-42` | Network errors return `status: 0` — non-standard convention. | Document or use error type discriminant. |
| 72 | frontend-ui | 8 | `svelte-frontend/src/lib/utils.ts:13-20` | `formatDate` function name vague — hardcodes `en-GB`. | Accept locale parameter with default. |
| 73 | library | 3 | `library/views.py:13,33,53` | Pagination disabled on all library list views. | Enable or document. |
| 74 | library | 3 | `library/urls/__init__.py:3` | Dead empty `urlpatterns` in `__init__.py`. | Remove or use as central include point. |
| 75 | library | 3 | `library/serializers.py:15` vs `models.py:23` | `SeriesSerializer` omits `created_at` field. | Add if intentional, remove from model if not. |
| 76 | architect | 10 | `reviews/models.py:26` | `Review.__str__` uses `self.user.username` — User has no `username` field. Raises `AttributeError`. | Fix to `self.user.handle`. |
| 77 | architect | 10 | `analysis/models.py:67` | Lazy `import ValidationError` inside model `clean()` method. | Move to top-level imports. |
| 78 | architect | 10 | `config/settings/dev.py:10` | `CELERY_TASK_ALWAYS_EAGER` hardcoded in dev — blocks real Celery testing. | Use env var. |
| 79 | overengineer | 11 | `books/serializers.py:35` | `BookSerializerMixin` with 3 short methods — over-ceremony for same-file usage. | Inline methods directly. |
| 80 | overengineer | 11 | `books/models.py:68` | `BookAuthor.role` field never read/written in any serializer. | Remove. |
| 81 | overengineer | 11 | `svelte-frontend/src/lib/utils.ts:4,8-28` | `cn()`, `formatRating()`, `formatDate()`, `initials()` — all unused. | Remove functions and unused dependencies. |
| 82 | overengineer | 11 | `users/urls/public.py`, `library/urls/{authors,series,genres}.py` | Single-endpoint/per-model URL files — 5 files for 7 routes. | Merge into one URL file per app. |
| 83 | overengineer | 11 | `config/test_helpers.py:4-13` | `AuthTestHelper` as class-mixin — simpler as pytest fixture. | Use pytest fixture. |
| 84 | overengineer | 11 | `config/pagination.py:5-28` | Custom `StandardPagination` renames DRF keys (`count→total`, `results→data`). | Use DRF default format, adapt frontend. |
| 85 | overengineer | 11 | Multiple files | ~15 `# noqa: N815` comments on camelCase serializer fields. | Add `N815` to ruff ignore in pyproject.toml. |
| 86 | overengineer | 11 | `config/settings/base.py:99-111` | 9 granular per-endpoint throttle scopes for hobby project. | Simplify to default DRF throttling. |

## 6. API Contract Matrix

| METHOD | Backend Path | api.generated.ts | user.ts | Status |
|--------|-------------|-----------------|---------|--------|
| POST | `/api/auth/register/` | ✓ `auth_register_create` | — | OK |
| POST | `/api/auth/login/` | ✓ `auth_login_create` | — | OK |
| POST | `/api/auth/refresh/` | ✓ `auth_refresh_create` | — | OK |
| POST | `/api/auth/logout/` | ✓ `auth_logout_create` | — | OK |
| GET | `/api/auth/me/` | ✓ `auth_me_retrieve` | — | OK |
| GET/PATCH/DELETE | `/api/users/me/` | ✓ `users_me_*` | `getCurrentUser` (GET) | ⚠️ Response `content?: never` |
| PATCH | `/api/users/me/password/` | ✓ | — | ⚠️ Response `content?: never` |
| PATCH | `/api/users/me/email/` | ✓ | — | ⚠️ Response `content?: never` |
| PATCH | `/api/users/me/avatar/` | ✓ | — | ⚠️ Response `content?: never` |
| PATCH | `/api/users/me/settings/` | ✓ | — | ⚠️ Response `content?: never` |
| POST | `/api/users/me/export/` | ✓ | — | ⚠️ Response `content?: never` |
| GET | `/api/users/{handle}/shelves/` | ✓ | — | OK |
| GET | `/api/users/{handle}/recently-read/` | ✓ | — | OK |
| POST/DELETE | `/api/users/{handle}/follow/` | ✓ | — | OK |
| GET | `/api/users/{handle}/followers/` | ✓ | — | OK |
| GET | `/api/users/{handle}/following/` | ✓ | — | OK |
| GET | `/api/u/{handle}/` | ✓ | — | OK |
| GET | `/api/books/` | ✓ | — | OK |
| GET | `/api/books/contains-character/` | ✓ | — | OK |
| GET | `/api/books/{pk}/` | ✓ `books_retrieve_2` | — | ⚠️ |
| GET | `/api/books/{id_or_slug}/` | ✓ `books_retrieve` | — | ⚠️ Response shape incomplete |
| GET/POST | `/api/books/{id_or_slug}/reviews/` | ✓ | — | OK |
| POST | `/api/books/{book_id}/characters/{cid}/merge/` | ✓ | — | OK |
| GET | `/api/shelf/` | ✓ | — | OK |
| GET/POST/PATCH/DELETE | `/api/shelf/{book_id}/` | ✓ | — | OK |
| GET/POST | `/api/shelf/me/collections/` | ✓ | — | OK |
| GET/PUT/PATCH/DELETE | `/api/shelf/me/collections/{slug}/` | ✓ | — | OK |
| POST/DELETE | `/api/shelf/me/collections/{slug}/books/{bid}/` | ✓ | — | OK |
| GET/POST | `/api/reviews/` | ✓ | — | OK |
| GET/PUT/PATCH/DELETE | `/api/reviews/{pk}/` | ✓ | — | OK |
| GET | `/api/authors/` | ✓ | — | OK |
| GET | `/api/authors/{pk}/` | ✓ | — | OK |
| GET | `/api/series/` | ✓ | — | OK |
| GET | `/api/series/{pk}/` | ✓ | — | OK |
| GET | `/api/genres/` | ✓ | — | OK |
| GET | `/api/genres/{pk}/` | ✓ | — | OK |
| POST | `/api/books/{bid}/ai/extract/` | ✓ | — | OK |
| GET | `/api/books/{bid}/ai/extraction/` | ✓ | — | OK |
| POST | `/api/books/{bid}/characters/{cid}/hide/` | ✓ | — | OK |

**Summary:** 38 endpoints, all present in `api.generated.ts`. Key issues: all `/api/users/me/*` endpoints lack response schemas (#17), BookDetail response wrapper undocumented (#16), and no frontend API consumption modules for non-user endpoints (#49).

## 7. ADR Compliance

| ADR | Decision | Code Compliance | Evidence | Notes |
|-----|----------|----------------|----------|-------|
| ADR-001 | JWT in HttpOnly cookies, no localStorage | ✅ Pass | `cookie_auth.py:14-23`, `hooks.server.ts:5-7` | Refresh handled by backend, but **client missing 401 auto-retry** (Critical #3) |
| ADR-001 | Authorization header fallback | ⚠️ Partial | `cookie_auth.py:16-18` overrides parent, drops header support | Accept but not critical |
| ADR-001 | Refresh token path-restricted | ✅ Pass | `cookie_auth.py:9` — `path=/api/auth/refresh/` | |
| ADR-001 | CSRF protection | ✅ Pass | `settings/base.py` — CSRF_TRUSTED_ORIGINS required in prod | |
| ADR-002 | Two Celery workers (NER + LLM) | ✅ Pass | `celery.py` — separate queues with task routing | |
| ADR-002 | DWA (Discrete Worker Architecture) | ✅ Pass | `ner_engine.py`, `llm_engine.py` — independent | |
| ADR-003 | Entities per-book, no global | ✅ Pass | All entities have `book` FK, `UniqueConstraint` includes `book` | Terminology: code uses `UniqueConstraint`, ADR says `unique_together` |
| ADR-003 | No Chapter model | ✅ Pass | Chapter model removed | |
| ADR-003 | 2-task pipeline (vs 5) | ✅ Pass | `analyse_book` + `relations_for_book` | Idempotence concern (Architecture Perspective 2, §3) |
| ADR-004 | Vue removed, SvelteKit adopted | ✅ Pass | No `.vue` files, no `import from 'vue'` | Frontend in early bootstrap phase |

## 8. Architecture Critique

### Perspective 1 — Defense of Current Architecture

The StoryShelf architecture is sound and well-justified for its scale. Six key decisions hold up under scrutiny:

**JWT via HttpOnly cookies (ADR-001)** is the correct security posture. `localStorage` tokens are exposed to any XSS payload; HttpOnly cookies are not. The cookie passthrough in SvelteKit (`hooks.server.ts:5-7`) is clean — Svelte never sees the JWT, only copies the `cookie` header to SSR fetches. Refresh token with `path=/api/auth/refresh/` minimizes exposure. Token blacklisting on password change is correct.

**Two separate Celery workers (ADR-002)** is technical necessity, not overengineering. spaCy's transformer models hold the GIL via BLAS operations — `prefork` pool is the only workable option. OpenRouter is pure I/O — `gevent` monkey-patching enables thousands of concurrent HTTP requests. Trying to merge them into one worker creates either a GIL bottleneck or a monkey-patch conflict with spaCy's C-extensions. Task routing via `CELERY_TASK_ROUTES` provides clean separation and independent scaling.

**Entities per-book, no Chapter model (ADR-003)** is the best architectural decision in the codebase. The prior design had 5 tasks with race conditions — a production catastrophe. `Chapter` was a leaky abstraction with no frontend consumer. `unique_together("name", "book")` solves the real problem of same-name characters across books. Chunking with 400-word overlap is an internal worker detail, not a database concern. Pipeline compression from 5→2 tasks reduces error surface by 60%.

**SvelteKit hard replace (ADR-004)** is correct. Two simultaneous frontends means double CI builds, double bugs, and routing complexity. Vue was temporary from the start. OpenAPI-generated types provide type safety and catch drift in CI.

**Code quality is consistently high**: all 6 Django apps share identical structure (`models.py`, `views.py`, `serializers.py`, `urls.py`, `tests/`), `full_clean()` is called in views where appropriate, `Prefetch` with `to_attr` avoids N+1, signals are used correctly for cross-app side effects, and `select_for_update()` protects merge operations from race conditions. 265 backend tests with zero failures at audit time.

**Infrastructure is appropriately simple**: RabbitMQ with DLX prevents message loss, Flower provides monitoring, `CELERY_TASK_ALWAYS_EAGER` in dev eliminates broker need locally, Docker Compose reproduces everything with one command, Caddy handles SSL automatically.

For a hobby/portfolio project with <10k books, this architecture has the right amount of engineering — enough to be correct, not so much that it becomes a maintenance burden.

### Perspective 2 — Counter-arguments & Alternatives

Several decisions have hidden costs that manifest at scale:

**`avg_rating` signals** (`reviews/signals.py:8-19`) perform a full `SELECT AVG() + COUNT()` on every `Review.save()`/`delete()`. At 10k reviews per book, that's 10k rows scanned in a synchronous signal handler. Signals are transactionally opaque — a rolled-back transaction after signal emission leaves `avg_rating` inconsistent. Bulk operations (`bulk_create`, `queryset.delete`) don't fire signals — `avg_rating` silently drifts. A materialized view with periodic refresh would scale infinitely; the current approach works for <100 reviews per book but is a time bomb.

**`Book.text` as `TextField` in main table** means every `SELECT *` (Django Admin, list views without `.defer()`) loads full book text into memory and across the network. `BookListView` doesn't `.defer("text")`. Text is cleared post-NLP, which mitigates this, but until analysis completes, it's a potential performance issue for large books.

**`find_sentences_with_both_characters` (`text_parser.py:17-28`)** is O(n² × m): for 100 characters and 30k sentences (a 500k-word book), that's ~150 million regex searches, all synchronous in the NER worker task. This will block the CPU-bound `celery-ner` worker for minutes. A positional index approach would reduce to O(m × c).

**Pipeline idempotence is missing** (`analysis/tasks.py`): re-analyzing a book accumulates entities — old characters stay, new ones are added. No `analysis_run_id`, no soft-delete of old results, no versioning. ADR-003 acknowledges this but the gap is larger than stated.

**No cache layer**: no Redis cache for book listing, user profiles, or NLP results. Every request hits the database. For a hobby project this is fine; at 10x traffic, caching cuts database load by 90%+.

**Frontend is minimal**: 3 routes, no error boundary (`+error.svelte` missing), no `+layout.server.ts`, auth flash on every navigation, cookie passthrough only works for SSR (client-side hydration uses browser's native cookie sending — which is actually correct for same-origin). The architecture is correct but incomplete.

**What would break at 10x scale:**
1. RabbitMQ+Celery on single VPS — NER queue grows faster than single worker clears (spaCy CPU-bound)
2. PostgreSQL result backend — JSONB for NLP results grows linearly with book count
3. `find_sentences_with_both_characters` O(n² × m) — multi-minute block on NER worker
4. `avg_rating` signals — full `AVG()` per review at thousands of reviews/day
5. No caching — database becomes bottleneck

**What a v2 rewrite would change:**
- `avg_rating` → PostgreSQL materialized view with periodic refresh
- `Book.text` → separate `BookContent` table
- Character co-occurrence → positional index, not O(n²) regex
- Pipeline → idempotent with `analysis_run_id` + soft-delete + versioning
- Frontend → Redis cache for frequently-read endpoints
- Workers → NER worker per CPU core, LLM worker with higher concurrency
- Monitoring → Sentry or Prometheus beyond Flower

## 9. Architect's Notes

### Dead Code

| # | File:Line | Item | Action |
|---|-----------|------|--------|
| D1 | `analysis/text_parser.py:31` | `split_into_chapters()` — defined, tested, never called | Remove |
| D2 | `analysis/text_stats.py:22` | `analyse_text()` — defined, tested, zero application callers | Remove |
| D3 | `analysis/models.py:61` | `BookCharacter.is_canonical` property — only referenced in tests | Remove or promote |
| D4 | `books/management/commands/` | Empty directory tree (2 init files, no commands) | Remove |
| D5 | `books/models.py:68` | `BookAuthor.role` field — never read/written in any serializer | Remove |
| D6 | `shelf/models.py:31-32` | `ShelfEntry.personal_rating` — never exposed via API serializer | Remove or add to serializer |
| D7 | `svelte-frontend/src/lib/utils.ts:4,8-28` | `cn()`, `formatRating()`, `formatDate()`, `initials()` — all unused | Remove + drop unused deps |

### Pattern Quality

**BAD:**

| # | File:Line | Pattern | Fix |
|---|-----------|---------|-----|
| B1 | `reviews/models.py:26` | `Review.__str__` uses nonexistent `self.user.username` → `AttributeError` | `self.user.handle` |
| B2 | `reviews/admin.py:10`, `shelf/admin.py:17` | Admin `search_fields` use `user__username` (no such field) | `user__handle` |
| B3 | `books/serializers.py` vs `analysis/serializers.py` | camelCase vs snake_case serialization of same models | Normalize to camelCase |
| B4 | `reviews/views.py:45-52,90-97` | Duplicated `IntegrityError` handling in two create views | Extract to shared method |
| B5 | `analysis/views.py:24`, `serializers.py:65` | Hardcoded status string `"pending"/"running"/"done"` instead of enum refs | Use `AIExtractionStatus.PENDING` etc. |
| B6 | `analysis/models.py:67` | Lazy `import ValidationError` inside method body | Move to top of file |
| B7 | `books/serializers.py:38` | `list(obj.authors.all())` forces full queryset evaluation | `obj.authors.first()` |
| B8 | `shelf/serializers.py:17` | `.exists()` then `.first()` — two queries for one check | `first() and check for None` |

**GOOD:**

- Clean app separation — 6 Django apps with well-defined responsibilities
- Consistent DRF class-based views with class-level permission declarations
- Signal-based cross-app updates (`avg_rating` via `reviews/signals.py`)
- Proper `UniqueConstraint` usage (not legacy `unique_together`)
- Transaction atomicity with `select_for_update()` for merge operations
- OpenAPI schema generation with TypeScript codegen
- Comprehensive test coverage (265 tests, 0 failures)
- Slug generation with collision handling across all models
- Config separation (dev/prod) with startup validation in prod
- 9 distinct rate-limit throttle scopes
- Idempotent APIs (`get_or_create` for shelf operations)

### Structural Observations

**Directory layout** is standard Django: each app has `models/views/serializers/urls/admin/apps/tests/migrations`. `analysis/` has submodules for engine implementations. `config/` houses project settings with `settings/` subpackage.

**Module boundaries are mostly clear but have cross-app coupling:** `books/views.py` imports `analysis.models.BookCharacter` (lazily) and `shelf.models.ShelfEntry`; `users/views.py` imports from 4 apps for public profile aggregation; `reviews/views.py` crosses into `books.lookups`. No circular dependencies detected. Dependency flow: `analysis → books ← reviews/shelf → users` (library is leaf).

**Naming inconsistency:** Serializer field naming splits between camelCase (`books/serializers.py`) and snake_case (`analysis/serializers.py`). URL organization splits between single-file (`reviews/urls.py`) and multi-file (`users/urls/auth.py,users.py,public.py`).

**Import patterns:** Consistent absolute imports for cross-app, relative for within-app. One lazy import for circular dependency avoidance. Star imports only in settings (standard Django).

**Frontend structure (early stage):** 8 files total. No component library, no routing beyond root. Bootstrap phase — consistent with Phase 2.7 roadmap.

## 10. Overengineering Report

### Premature Abstractions

| # | File:Line | Finding | Alternative |
|---|-----------|---------|-------------|
| OE1 | `analysis/serializers.py:6` & `books/serializers.py:8` | Duplicate `BookCharacterSerializer` in two files | Consolidate to one |
| OE2 | `analysis/serializers.py:20` & `books/serializers.py:21` | Duplicate `CharacterRelationSerializer` | Consolidate |
| OE3 | `books/serializers.py:35` | `BookSerializerMixin` with 3 short methods | Inline |

### YAGNI Violations

| # | File:Line | Finding | Alternative |
|---|-----------|---------|-------------|
| OE4 | `analysis/models.py:81-96` | `BookPlace` model — NER-populated, zero API exposure | Remove or expose |
| OE5 | `analysis/models.py:98-112` | `BookOrganization` — same as above | Remove or expose |
| OE6 | `analysis/text_parser.py:31-42` | `split_into_chapters()` — dead code | Remove |
| OE7 | `analysis/text_stats.py:22-36` | `analyse_text()` — dead code | Remove |
| OE8 | `shelf/models.py:31-32` | `personal_rating` field never exposed | Remove or add to serializer |
| OE9 | `books/models.py:68` | `BookAuthor.role` never read/written | Remove |
| OE10 | `svelte-frontend/src/lib/utils.ts:4-28` | 4 unused utility functions + 2 unused deps | Remove |
| OE11 | `library/models.py:43` | Tag model — no API exposure | Expose or remove |

### Excessive Indirection

| # | File:Line | Finding | Alternative |
|---|-----------|---------|-------------|
| OE12 | `users/urls/public.py` | Single-endpoint URL file (7 lines) | Merge into `users/urls.py` |
| OE13 | `library/urls/{authors,series,genres}.py` | 3 identical 8-line URL files | Merge into `library/urls.py` |
| OE14 | `config/test_helpers.py` | `AuthTestHelper` class-mixin | pytest fixture |
| OE15 | `reviews/serializers.py:28-59` | Two nearly-identical review create serializers | Use context to omit `bookId` |

### Complexity for Complexity's Sake

| # | File:Line | Finding | Alternative |
|---|-----------|---------|-------------|
| OE16 | `config/pagination.py:5-28` | Custom `StandardPagination` — just renames DRF keys | Use DRF defaults |
| OE17 | Multiple files | ~15 `# noqa: N815` comments | Configure ruff ignore once |

### Scale Mismatch

| # | File:Line | Finding | Alternative |
|---|-----------|---------|-------------|
| OE18 | `config/celery.py` + `settings/base.py:137-148` | Celery+RabbitMQ+Redis for 2 async tasks | `threading.Thread` or `django-rq` |
| OE19 | `config/settings/base.py:99-111` | 9 granular throttle scopes for hobby project | Default DRF throttling |

## 11. Metrics

| Metric | Value |
|--------|-------|
| **Backend** | |
| Python application files | ~50 (excluding migrations) |
| Test files | 15 |
| Total tests | 265 |
| Tests passed | 265 |
| Tests failed | 0 |
| Tests skipped | 0 |
| Pre-existing lint errors (ruff) | 0 |
| Pre-existing OpenAPI warnings (drf-spectacular) | ~60 (all JWTCookieAuthentication/serializer type hint warnings — pre-existing, cosmetic) |
| **Frontend** | |
| Svelte files | 3 |
| TypeScript files | 6 |
| Svelte-check errors | 0 |
| Svelte-check warnings | 0 |
| ESLint errors | 0 |
| Prettier formatting issues | 0 |
| **API Contract** | |
| Backend endpoints | 38 |
| Endpoints in api.generated.ts | 38 (100%) |
| Endpoints with missing response schema | 11 (all `/api/users/me/*` endpoints) |
| Endpoints with incomplete response shape | 1 (BookRetrieve wrapper) |
| Endpoints with no frontend consumer | 37 of 38 (only `/users/me/` called, rest unimplemented) |
| **Code Quality** | |
| Dead code instances (unused functions/fields) | 13 |
| Overengineering instances | 19 |
| Active bugs (crash-capable) | 3 (`Review.__str__`, 2x admin `user__username`) |
| Critical audit findings | 3 |
| High audit findings | 18 |
| Medium audit findings | 32 |
| Low audit findings | 33 |
| **Total findings (all agents, deduplicated)** | **86** |

## 12. Priority Recommendations

1. **Fix 3 critical issues first** (before production use):
   - Race condition in `avg_rating` signal → `select_for_update()` or materialized view
   - Default `is_hidden` filtering on BookCharacter → custom manager
   - 401 auto-retry in frontend `_client.ts` → intercept + refresh + retry

2. **Fix active bugs** (will crash at runtime):
   - `Review.__str__` → `self.user.handle` (not `.username`)
   - Admin `search_fields` → `user__handle` (reviews + shelf admin)

3. **Normalize serialization convention**: pick camelCase for JSON API surface, apply consistently across all 6 apps. This eliminates the `BookList.ratings_count` vs `BookDetail.ratingsCount` type mismatch and ensures frontend code doesn't handle two field names for the same data.

4. **Complete OpenAPI schemas**: add `@extend_schema` decorators to all `APIView`-based views (`UserMeView`, `PasswordChangeView`, etc.) so `drf-spectacular` generates response schemas. Regenerate `api.generated.ts`.

5. **Add `+layout.server.ts`** to SvelteKit frontend — loads current user once, eliminates N+1 API calls per navigation, prevents auth flash. Add `+error.svelte` for error boundaries.

6. **Clean up dead code**: remove `split_into_chapters`, `analyse_text`, `BookAuthor.role`, unused frontend utilities, empty management command directories, dead `BookPlace`/`BookOrganization` models (or expose via API).

7. **Add pagination** to currently unlimited endpoints: `ReviewListCreateView`, `ShelfListView`, `MyShelvesView`, all library list views.

8. **Document relationship asymmetry**: explicitly state whether `CharacterRelationship` is directional-only or should create reciprocal rows for symmetric types.

9. **Add missing tests**: signal on review update, partial delete count recalculation, BookPlace/Organization constraints, source/confidence validation, Serie/Genre uniqueness.

10. **Defer scale concerns**: the `Book.text` in main table, Celery infrastructure overhead, and `find_sentences_with_both_characters` O(n²) complexity are non-issues at current scale. Address when book count or traffic grows 10x.
