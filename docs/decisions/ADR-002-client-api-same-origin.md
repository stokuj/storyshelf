# ADR-002: Client-side API is same-origin `/api`, reverse-proxied to Django in every environment

- **Status:** Accepted
- **Date:** 2026-05-30
- **Related:** [ADR-001](ADR-001-jwt-httponly-cookies.md) (JWT HttpOnly cookies)

## Context

The frontend (SvelteKit, SSR) and the backend (Django/DRF) are separate services. There are two distinct request paths:

- **Server-side** (SSR `load`, form actions): runs in the SvelteKit Node process, calls Django directly via `INTERNAL_API_URL` (e.g. `http://django:8000/api`). Never goes through the browser.
- **Client-side** (browser `fetch` in event handlers — rating, add-to-shelf, status change, delete): runs in the browser and must obey the browser's same-origin and CSP rules.

The client-side path is constrained:

- The production CSP sets `connect-src 'self'` (see `infra/caddy/Caddyfile`), so the browser may **only** call the page's own origin. A cross-origin call to `http://django:8000` is forbidden.
- JWT auth uses HttpOnly cookies ([ADR-001](ADR-001-jwt-httponly-cookies.md)); cookies ride along automatically only when the request is same-origin.

Therefore client-side code in `svelte-frontend/src/lib/api/_client.ts` uses a hard-coded, **relative `/api`** base (not `PUBLIC_API_URL`). For this to work, *something on the frontend origin* must reverse-proxy `/api/*` to Django.

In production this is Caddy (`handle_path /api/* → reverse_proxy django:8000`, everything else → the SvelteKit server). The dev environment, however, exposed the SvelteKit dev server directly on `:5174` with **no reverse proxy**, so client-side `/api` calls 404'd. This stayed latent through M1–M2 (whose authenticated writes all go through SSR form actions) and only surfaced in M3, the first feature with client-side mutations (`/shelf`): "Failed to add to shelf" was a `/api` routing 404, not an app bug.

## Decision

**Client-side API calls are always same-origin, relative `/api`, and that path is reverse-proxied to Django in every environment.** Concretely:

1. **Client code** never uses an absolute API URL or `PUBLIC_API_URL` for browser fetches — always relative `/api` via `apiFetch(...)`. (`PUBLIC_API_URL` exists only as a legacy/SSR fallback.)
2. **Server-side** code (SSR/actions) calls Django directly via `INTERNAL_API_URL`.
3. **Production / Docker prod:** Caddy reverse-proxies `/api/*` → `django:8000` (single origin).
4. **Dev:** the SvelteKit dev server mirrors Caddy via `server.proxy['/api'] → INTERNAL_API_URL (or localhost:8000)` in `vite.config.ts`. This covers both bare `npm run dev` and the Docker `svelte` container (which runs `vite dev`). `server.proxy` is dev-only and has no effect on the adapter-node production build.

We chose a **Vite dev proxy** over adding Caddy to the dev compose: it restores the same-origin `/api` contract with ~3 lines, no extra container, no dev TLS, no HMR-through-proxy tuning, and no change to the `:5174` workflow. Adding Caddy to dev would give byte-identical topology but costs a dev-specific Caddyfile (prod targets `svelte:3000`, dev is `:5174`), HMR WebSocket config, and a port change — not worth it for this project.

## Consequences

- Dev and prod share the same client contract (same-origin `/api`), so a route that works in dev works in prod. The dev/prod parity gap that caused the M3 bug is closed.
- CSP-compatible and cookie-compatible by construction; no CORS, no `SameSite=None`.
- **Regression guard:** the `/shelf` E2E (`svelte-frontend/e2e/shelf-status.spec.ts`) exercises client-side mutations end-to-end (routing + cookies + auth + token refresh through the proxy). If client-side `/api` ever breaks again, that suite fails instead of failing silently in the browser.
- **Running E2E:** needs the dev stack (Django on `:8000` + seeded books) and the Vite proxy (now default). Because a full run registers several users, relax the register throttle for the E2E Django server via the existing env knob: `THROTTLE_AUTH_REGISTER=1000/min` (no code change — base settings already read it). E2E is not part of CI / `make verify`; run it with `npm run test:e2e`.
- **Anti-pattern (do not do):** pointing client-side fetches at an absolute `http://localhost:8000` to "skip the proxy" — it violates the prod CSP `connect-src 'self'`, breaks cookies, and tests a topology you don't ship.
