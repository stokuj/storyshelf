## Why

Frontend had 19 technical bugs — from critical (production broken by missing nginx proxy, dead review function) through important (auth guard on F5 doesn't wait for token, no lazy loading) to polish (no mobile menu, wrong date format).

## What

Three waves of fixes in 6 commits + code review fixes.

**Wave 1 (critical)**
- Nginx proxy for `/api/`, `/admin/`, `/static/` + `.dockerignore`
- Review form and "Remove from shelf" button in BookDetailView
- Network error handling in `api.js`
- Token synchronization with localStorage (reads on every call instead of one-shot `let`)
- Deterministic review sorting (newest first instead of random)
- Skeleton loaders in HomeView and BookDetailView

**Wave 2 (important)**
- Lazy loading of all views, auth guards, scroll behavior
- Sourcemaps in production build
- Separate `useAsyncState` instances for loading vs mutations in BookshelfView

**Wave 3 (polish)**
- Mobile hamburger menu
- Date format without time portion
- URL update after username change
- Dynamic `<title>` per route
- Nginx gzip, cache headers, security headers (CSP, X-Frame-Options)

**Code review**
- `location ^~` in nginx — higher priority than regex for assets
- `beforeEach` async with `await refreshAuth()` — fix for F5 redirect to login
- Removed dead code (`changeShelfStatus`)

## How

Standard Vue 3 SPA changes + nginx config. No Django backend changes.

## Testing

- `npm run build` — 39 modules transformed, chunks per view, sourcemaps
- Skeleton loaders preserve layout shape before data loads
- Auth guard: logged-in user is NOT redirected to login on F5 at `/bookshelf`
- `curl http://localhost:5173/api/books/` returns data through Vite proxy

## Rollback

Revert commits — each is atomic and independent.

## Risk

Low — frontend and nginx only, no API contract changes. CSP `default-src 'self'` may block external assets — extend if needed.
