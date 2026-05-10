# Design: P1 Frontend Fixes (Issue #23)

## Overview

Three independent frontend fixes bundled in one issue:
1. BookDetailView — missing fallback when book not found (null details)
2. ProfileView — missing fallback when user not found (null profile)
3. Frontend `/health` endpoint — missing for Docker container probes

## 1. NotFoundState Component

### New file: `frontend/src/components/NotFoundState.vue`

A reusable "not found" component used in both BookDetailView and ProfileView.

**Props:**
- `title` (string, required) — heading e.g. "Książka nie istnieje"
- `message` (string, optional) — supplementary description
- `homeLink` (boolean, default `true`) — whether to show "back to home" button

**Template:**
- SVG icon (book/question mark)
- `<h2>` with `title` prop
- `<p>` with `message` prop (if provided)
- `<RouterLink to="/">` as "Wróć do strony głównej" button (if `homeLink` is true)

### Changes to BookDetailView.vue

After `v-else-if="details"` block (line 213), add `v-else`:

```html
<template v-else>
  <NotFoundState
    title="Książka nie istnieje"
    message="Nie znaleziono książki o podanym identyfikatorze."
  />
</template>
```

The existing template structure:
- `v-if="error"` → error alert
- `v-else-if="loading"` → loading spinner
- `v-else-if="details"` → book content
- **`v-else`** → NotFoundState (NEW)

### Changes to ProfileView.vue

After `v-else-if="profile"` block (line 58), add `v-else`:

```html
<template v-else>
  <NotFoundState
    title="Użytkownik nie znaleziony"
    message="Profil o podanej nazwie nie istnieje."
  />
</template>
```

The existing template structure:
- `v-if="error"` → error alert
- `v-else-if="loading"` → loading spinner
- `v-else-if="profile"` → profile content
- **`v-else`** → NotFoundState (NEW)

## 2. Health Endpoint

### Dev (Vite dev server)

Add middleware in `frontend/vite.config.js`:

```js
configureServer(server) {
  server.middlewares.use('/health', (_req, res) => {
    res.statusCode = 200
    res.end('OK')
  })
}
```

Responds with `200 OK` on `GET /health` without invoking Vue rendering.

### Prod (nginx inside container)

Add to `frontend/nginx.conf`:

```
location /health {
    return 200 "OK";
    add_header Content-Type text/plain;
}
```

### Docker Compose healthchecks

Add to both `docker-compose.dev.yml` and `docker-compose.prod.yml` frontend services:

**Dev:**
```yaml
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://localhost:5173/health"]
  interval: 10s
  timeout: 3s
  retries: 5
```

**Prod:**
```yaml
healthcheck:
  test: ["CMD", "wget", "-qO-", "http://localhost:80/health"]
  interval: 10s
  timeout: 3s
  retries: 5
```

Note: The prod container uses `nginx:1.27-alpine` which has `wget` available. The dev container uses `node:20-alpine` which also has `wget`.

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/NotFoundState.vue` | New — shared not-found component |
| `frontend/src/views/BookDetailView.vue` | Add `v-else` with NotFoundState |
| `frontend/src/views/ProfileView.vue` | Add `v-else` with NotFoundState |
| `frontend/vite.config.js` | Add health middleware |
| `frontend/nginx.conf` | Add health location block |
| `infra/compose/docker-compose.dev.yml` | Add frontend healthcheck |
| `infra/compose/docker-compose.prod.yml` | Add frontend healthcheck |

## Non-Goals

- No changes to backend API
- No changes to Caddy reverse proxy config
- No changes to other views
