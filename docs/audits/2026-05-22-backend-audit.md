# Backend Audit — 2026-05-22

**Scope:** `backend-django/`, `infra/compose/`, `infra/caddy/`, `infra/scripts/`  
**Tests run:** 181 passed, ruff clean, coverage 92%  
**Previous audit:** `docs/superpowers/specs/2026-05-13-django-audit.md`

---

## Executive Summary

Backend is functionally solid, well-tested (92% coverage), and lint-clean. Most issues from the previous May 13 audit spec have been resolved (model constraints, validators, DB indexes, ruff config). **However, there are production deployment and security configuration gaps** that must be fixed before going live.

---

## Critical Issues

### 1. SECURE_SSL_REDIRECT + missing SECURE_PROXY_SSL_HEADER = redirect loop in production

- `config/settings/prod.py:6` sets `SECURE_SSL_REDIRECT = True`
- Caddy terminates SSL and proxies to Django over plain HTTP
- Django sees every request as HTTP and issues an infinite `301 → https://...` redirect

**Fix:** add `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` to `prod.py` (Caddy sends `X-Forwarded-Proto` by default).

---

### 2. Caddyfile uses `:80` with `tls internal` in production

- `infra/caddy/Caddyfile:1-2` listens on `:80` with self-signed (`tls internal`) certificates
- Production requires a real domain + automatic Let's Encrypt. With `:80` Caddy will never request a public certificate.

**Fix:** replace `:80` with the production domain name (e.g. `storyshelf.example.com`) and remove `tls internal`.

---

### 3. Flower monitoring exposed without authentication in production

- `docker-compose.prod.yml:74-85` exposes Flower on port `5555` inside the Docker network, but there is **no Caddy route** and **no basic auth** configured
- Anyone with access to the VPS network (or a mistakenly forwarded port) can inspect Celery tasks, broker URLs, and retry failed tasks

**Fix:** add a Caddy route with basic auth, or bind Flower to `127.0.0.1:5555` and tunnel via SSH.

---

## Important Issues

### 4. LLM engine lacks HTTP timeout

- `analysis/llm_engine.py:78-88` calls `openai.chat.completions.create()` without a `timeout` parameter
- Default OpenAI client timeout is 600 s — a hung worker blocks the gevent pool for 10 minutes

**Fix:** add `timeout=30` (or env-driven) to the `chat.completions.create()` call.

---

### 5. NER engine does not catch exceptions inside `nlp.pipe()`

- `analysis/ner_engine.py:74` iterates over `nlp.pipe(chunks, batch_size=8)` without a try/except
- A corrupted spaCy model or unexpected token can crash the **celery-ner** worker process entirely

**Fix:** wrap the `for doc in nlp.pipe(...)` loop in a try/except that logs the error and returns empty entities.

---

### 6. Book detail endpoint performs an extra SQL query for shelf entry

- `books/serializers.py:96-105` does `instance.shelf_entries.get(user=request.user)`
- `BookRetrieveView.get_queryset` prefetches `authors`, `tags`, `genres`, `characters`, `character_relationships` **but not** `shelf_entries`
- Result: one extra `SELECT` on every authenticated book-detail request

**Fix:** add `.prefetch_related("shelf_entries")` in the view queryset and filter in Python, or use a `SerializerMethodField` with `Prefetch`.

---

### 7. Missing Content-Security-Policy (CSP) header

- `Caddyfile:29-33` sets `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`
- There is **no** `Content-Security-Policy` header. With a Vue SPA and external LLM API calls this is a notable omission.

**Fix:** add a restrictive CSP via Caddy or Django (`django-csp` package). The project already depends on `django-cors-headers`; `django-csp` is the natural complement.

---

### 8. Dev JWT signing key below recommended length (warning)

- Tests emit `InsecureKeyLengthWarning: The HMAC key is 22 bytes long` (dev-only key `dev-not-for-production`)
- This is **not** a production risk because `prod.py` enforces a real `DJANGO_SECRET_KEY`, but the dev experience is noisy.

**Fix:** use a longer dummy key in `dev.py` (≥32 bytes).

---

## Minor Issues

### 9. `deploy.sh` does not validate `.env` file presence

- `infra/scripts/deploy.sh:14-15` runs `docker compose pull` and `up -d --force-recreate` without checking that `.env` exists
- Missing `.env` causes containers to start with empty secrets / default passwords

**Fix:** add a guard: `if [ ! -f .env ]; then echo "Missing .env"; exit 1; fi`

---

### 10. `seed.py` sets hard-coded `avg_rating` and `ratings_count`

- `infra/scripts/seed.py:287-288` seeds `avg_rating` and `ratings_count` directly on the `Book` model
- The signal that recalculates these fields on review creation will overwrite them anyway, but the seed script bypasses model business logic. This is acceptable for a seed script, but should be documented.

---

### 11. `analysis/tasks.py` does not handle `Book.DoesNotExist` with return code

- `analyse_book` returns `None` silently when a book does not exist (`logger.warning`). In a monitoring context a non-zero Celery task state would be more useful.
- **Risk:** low — Flower shows the task as `SUCCESS` even though nothing happened.

---

## Resolved Since Previous Audit (2026-05-13)

| Item | Status |
|------|--------|
| `Book.isbn` `unique=True` | ✅ Fixed |
| `Author.name` `unique=True` | ✅ Fixed |
| `Book.title` `blank=True` removed | ✅ Fixed (now `CharField` without `blank=True`) |
| `MinValueValidator` on `Book.year` / `page_count` | ✅ Fixed |
| `ShelfEntry.clean()` date validation | ✅ Fixed + tested |
| `db_index` on `Review.book`, `Review.user`, `ShelfEntry` FKs | ✅ Fixed |
| ruff lint errors (I001, E501, N815) | ✅ Clean (`ruff check .` passes) |
| `pytest-cov` added to dev deps | ✅ Fixed |
| Review create validates `book_id` existence (400 not 500) | ✅ Fixed |
| Signal tests for `avg_rating` | ✅ Added |
| Genre endpoint tests | ✅ Added |
| `UserVisibilityView` tests | ✅ Added |

---

## Metrics

| Metric | Value |
|--------|-------|
| Total tests | 181 (142 Django + 39 pytest) |
| Ruff violations | 0 |
| Coverage | 92% |
| Production-ready blockers | 3 (#1, #2, #3) |
| High-priority fixes | 5 (#4, #5, #6, #7, #8) |

---

## Priority Recommendations

1. **CRITICAL** — Fix `SECURE_SSL_REDIRECT` + add `SECURE_PROXY_SSL_HEADER` in `prod.py`
2. **CRITICAL** — Replace `:80` with production domain in `Caddyfile` for real TLS
3. **CRITICAL** — Add authentication or bind-to-localhost for Flower in production
4. **HIGH** — Add `timeout` to OpenRouter API call in `llm_engine.py`
5. **HIGH** — Wrap `nlp.pipe()` in try/except in `ner_engine.py`
6. **HIGH** — Prefetch `shelf_entries` in `BookRetrieveView` to remove extra SQL query
7. **MEDIUM** — Add CSP header (Caddy or Django)
8. **MEDIUM** — Use longer dummy `SECRET_KEY` in `dev.py` to silence JWT warning
9. **LOW** — Add `.env` existence check to `deploy.sh`
10. **LOW** — Document that `seed.py` bypasses `avg_rating` signal logic

---

## Verification Commands

```bash
cd backend-django/
uv run ruff check .
DJANGO_ENV=dev uv run python manage.py test
DJANGO_ENV=dev uv run python manage.py migrate --check
DJANGO_ENV=dev uv run python -m pytest --cov --cov-report=term-missing
```
