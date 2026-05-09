# Fix Caddy routing: storyweave-api → nlp-service

## Problem

Caddyfile reverse-proxy targets `storyweave-api:8000`, but the Docker Compose service
is named `nlp-service`. Docker DNS resolves by **service name**, not `container_name`,
so the NLP service is completely unreachable in production.

## Solution

### Affected files

| File | Change |
|------|--------|
| `infra/caddy/Caddyfile` | 4 occurrences of `storyweave-api:8000` → `nlp-service:8000` |
| `infra/compose/docker-compose.prod.yml` | `container_name: storyweave-api` → `container_name: nlp-service` |

### Explicitly NOT changed

- `celery-worker` with `container_name: storyweave-celery-worker` — not referenced by Caddy
- `docker-compose.dev.yml` — Caddy is not used in dev

## Verification

```bash
make prod-up && curl http://localhost/api/docs
```

Expected: NLP service Swagger docs response. Previously: connection error / empty response.

## Rollback

Revert the 5-line diff in those two files and restart the stack.
