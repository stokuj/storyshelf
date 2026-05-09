# Fix Caddy Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all `storyweave-api:8000` references with `nlp-service:8000` in Caddyfile and align `container_name` in docker-compose.prod.yml.

**Architecture:** Simple string replacement in two config files. Docker DNS resolves by service name (`nlp-service`), not `container_name`. Fixing both the Caddyfile targets and the `container_name` ensures consistency.

**Tech Stack:** Caddy v2, Docker Compose

---

### Task 1: Fix Caddyfile reverse-proxy targets

**Files:**
- Modify: `infra/caddy/Caddyfile:4,9,13,34`

- [ ] **Step 1: Replace all 4 occurrences of `storyweave-api:8000` with `nlp-service:8000`**

Replace on each line:
- Line 4: `storyweave-api:8000` → `nlp-service:8000`
- Line 9: `storyweave-api:8000` → `nlp-service:8000`
- Line 13: `storyweave-api:8000` → `nlp-service:8000`
- Line 34: `storyweave-api:8000` → `nlp-service:8000`

Expected final Caddyfile content for affected blocks:

```caddy
:80 {
    handle /api/docs {
        rewrite * /docs
        reverse_proxy nlp-service:8000
    }

    handle /api/docs/* {
        uri strip_prefix /api
        reverse_proxy nlp-service:8000
    }

    handle /openapi.json* {
        reverse_proxy nlp-service:8000
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
        reverse_proxy nlp-service:8000
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

- [ ] **Step 2: Verify no remaining references to `storyweave-api`**

Run: `rg storyweave-api infra/caddy/Caddyfile`
Expected: no matches

- [ ] **Step 3: Commit**

```bash
git add infra/caddy/Caddyfile
git commit -m "fix: replace storyweave-api with nlp-service in Caddyfile"
```

---

### Task 2: Align container_name in docker-compose.prod.yml

**Files:**
- Modify: `infra/compose/docker-compose.prod.yml:32`

- [ ] **Step 1: Replace `container_name: storyweave-api` with `container_name: nlp-service`**

```yaml
  nlp-service:
    image: ghcr.io/stokuj/storyshelf-nlp:main
    container_name: nlp-service
    expose:
      - "8000"
```

- [ ] **Step 2: Commit**

```bash
git add infra/compose/docker-compose.prod.yml
git commit -m "fix: align nlp-service container_name with service name"
```

---

### Task 3: Verify routing fix

- [ ] **Step 1: Bring up the production stack**

```bash
make prod-up
```

- [ ] **Step 2: Test NLP service endpoint**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/docs
```
Expected: HTTP `200`

- [ ] **Step 3: Test backend endpoints still work**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost/api/books
curl -s -o /dev/null -w "%{http_code}" http://localhost/docs
```
Expected: HTTP `200` for both (or expected app-level response codes)

- [ ] **Step 4: Tear down**

```bash
make prod-down
```
