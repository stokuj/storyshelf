Design for a wave-based technical bug-fix pass on the StoryShelf Vue 3 frontend. Covers 19 bugs split into three atomic commits: critical, important, and polish.

**Attention Conservation Notice**
For: Whoever implements the frontend fix loop
What: Exact scope, file targets, and acceptance criteria for 19 frontend technical fixes
Action: Read the Wave Breakdown section, then proceed to the writing-plans skill
Skip if: You are looking for UI/UX redesign work (that is Stage 2, not this doc)

## Before You Start

- Branch from latest `main`. Do not work on `main` directly.
- This spec assumes the Django backend is already running and all endpoints exist. Only frontend code changes.
- All changes target files inside `frontend/src/` plus `frontend/nginx.conf`, `frontend/Dockerfile.prod`, `frontend/.dockerignore`, and `frontend/vite.config.js`.

## Wave Breakdown

### Wave 1 — Critical Fixes

These four items block production use or break core features.

#### 1.1 Nginx production proxy missing
**File:** `frontend/nginx.conf`, `frontend/Dockerfile.prod`
**Problem:** The production Nginx only serves static SPA files. It does not proxy `/api`, `/admin`, or `/static` to the Django backend.
**Fix:** Add `location /api/`, `/admin/`, and `/static/` blocks that `proxy_pass` to `http://django:8000` (the Django service name inside Docker Compose).
**Acceptance:** `curl http://localhost/api/books/` from inside the prod container returns data, not a 404.

#### 1.2 BookDetailView missing review form
**File:** `frontend/src/views/BookDetailView.vue`
**Problem:** The `<script>` defines `submitReview`, `reviewForm`, and `createBookReview`, but the `<template>` has no form.
**Fix:** Add a card below the book description with a star rating input (1-5), a textarea for content, and a submit button. Disable the button while `reviewLoading` is true. Show `reviewError` and `reviewMessage` in alert banners above the form.
**Acceptance:** A logged-in user can submit a review and sees it appear in the reviews list.

#### 1.3 BookDetailView missing "Remove from shelf" button
**File:** `frontend/src/views/BookDetailView.vue`
**Problem:** `removeShelfEntry` exists in script but no UI element calls it.
**Fix:** Add a "Usuń z półki" button next to the status select. Show it only when `details.shelfEntry` exists. On click, call `removeShelfEntry` and clear the select.
**Acceptance:** Clicking the button removes the book from the shelf and resets the status select to default.

#### 1.4 Network error handling in api.js
**File:** `frontend/src/api.js`
**Problem:** `fetch` failures (no connection, DNS error, CORS block) throw unhandled exceptions. The UI hangs on "Ładowanie...".
**Fix:** Wrap the `fetch` call inside `request()` in a `try/catch`. On catch, throw a user-friendly error ("Brak połączenia z serwerem.").
**Acceptance:** Disconnect the backend, reload a view, and see a readable error message instead of an infinite spinner.

### Wave 2 — Important Fixes

These six items degrade reliability, security, or developer experience.

#### 2.1 Trailing slash in visibility endpoint
**File:** `frontend/src/api.js`
**Problem:** `updateCurrentUserVisibility` calls `/api/users/me/visibility?...` without a trailing slash. Django returns a 301 redirect for PATCH, which some clients mishandle.
**Fix:** Change the path to `/api/users/me/visibility/?...`.
**Acceptance:** The PATCH request returns 200, not 301.

#### 2.2 Shared async state in BookshelfView
**File:** `frontend/src/views/BookshelfView.vue`
**Problem:** `loadBookshelf` and `changeStatus` reuse the same `useAsyncState` instance. Errors from one overwrite the other.
**Fix:** Create two separate `useAsyncState()` instances: one for initial load, one for mutations. Display each error in its own context.
**Acceptance:** An error during status change does not erase a load error and vice versa.

#### 2.3 Lazy loading and auth guards in router
**File:** `frontend/src/router.js`
**Problem:** All views are eagerly imported. There are no route guards for `/bookshelf` or `/settings`.
**Fix:** Convert all route components to `() => import('./views/...View.vue')`. Add a global `beforeEach` guard that redirects unauthenticated users from `/bookshelf` and `/settings` to `/login?next=<path>`.
**Acceptance:** `/settings` opened in an incognito window redirects to login. The main bundle size is smaller.

#### 2.4 Access token synchronization
**File:** `frontend/src/api.js`
**Problem:** `accessToken` is a module-level `let` initialized once at import. If localStorage changes in another tab, the old token is still used.
**Fix:** Read `localStorage.getItem('access_token')` inside `request()` before each call, instead of relying on the module variable.
**Acceptance:** Log in in Tab A, open Tab B, log out in Tab B, then perform an action in Tab A. Tab A gets a 401 and redirects to login.

#### 2.5 Scroll to top on navigation
**File:** `frontend/src/router.js`
**Problem:** After navigating, the scroll position stays at the previous page's offset.
**Fix:** Add `scrollBehavior: () => ({ top: 0 })` to the router options.
**Acceptance:** Navigate from a scrolled book list to a detail page. The detail page loads at the top.

#### 2.6 Source maps in production build
**File:** `frontend/vite.config.js`
**Problem:** No source maps are generated, making production debugging impossible.
**Fix:** Add `build: { sourcemap: true }` inside `defineConfig`.
**Acceptance:** After `npm run build`, `dist/assets/*.map` files exist.

### Wave 3 — Polish Fixes

These nine items fix smaller UX glitches, inconsistencies, and missing infra.

#### 3.1 Request cancellation with AbortController
**File:** `frontend/src/api.js`
**Problem:** Rapid navigation can leave pending requests running, causing race conditions.
**Fix:** Add an optional `signal` parameter to `request()`. In views that re-fetch on route change (e.g., `BookDetailView`), create an `AbortController` in `onMounted`, pass its signal to the request, and abort in `onUnmounted`.
**Acceptance:** Navigate quickly between book detail pages. Only the last page's data is rendered.

#### 3.2 Date format in ProfileView
**File:** `frontend/src/views/ProfileView.vue`
**Problem:** `formatDate` uses `timeStyle: 'short'`, showing the hour next to "Członek od".
**Fix:** Remove `timeStyle` and keep only `dateStyle: 'medium'`.
**Acceptance:** The label shows "Członek od 12 maja 2023" without an hour.

#### 3.3 Username change URL update
**File:** `frontend/src/views/SettingsView.vue`
**Problem:** After changing username, the browser URL still shows the old one. A refresh causes a 404.
**Fix:** After a successful save, call `router.replace(`/profile/${newUsername}`)` if the username changed.
**Acceptance:** Change username, save, refresh. The profile loads correctly.

#### 3.4 Dynamic page titles
**File:** `frontend/src/router.js`, `frontend/src/App.vue`
**Problem:** The `<title>` is always "StoryShelf".
**Fix:** Add a `meta.title` field to each route. In `router.afterEach`, read it and set `document.title` (e.g., "StoryShelf — Katalog książek").
**Acceptance:** Each route shows a distinct, Polish-language title.

#### 3.5 Nginx compression and security headers
**File:** `frontend/nginx.conf`
**Problem:** No gzip, no cache headers for hashed assets, no security headers.
**Fix:** Enable `gzip` for JS/CSS/JSON. Add `Cache-Control: immutable` for files matching `*-[hash].*`. Add `X-Frame-Options: DENY` and `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'`.
**Acceptance:** `curl -I` on a hashed asset shows `Cache-Control`. `curl -I` on `/` shows security headers.

#### 3.6 Deterministic review ordering
**File:** `frontend/src/views/BookDetailView.vue`
**Problem:** `randomReviews` shuffles on every load. Users see different reviews after refresh or back-navigation.
**Fix:** Replace `pickRandomReviews` with deterministic sorting (e.g., newest first, `createdAt` descending). Limit to 6.
**Acceptance:** Refreshing the same book always shows the same top reviews in the same order.

#### 3.7 Trailing slash audit
**File:** `frontend/src/api.js`
**Problem:** Some paths may still lack trailing slashes.
**Fix:** Audit every path in `api.js`. Ensure all end with `/`. The visibility fix in 2.1 covers the known case; this is a full audit.
**Acceptance:** Every `request()` call uses a path ending with `/`.

#### 3.8 Mobile responsive navbar
**File:** `frontend/src/App.vue`
**Problem:** On narrow screens, navbar links may wrap or overflow.
**Fix:** Add a hamburger menu for screens below `md`. Use a DaisyUI `dropdown` or collapsible drawer. Show/hide with a reactive `menuOpen` flag.
**Acceptance:** At 375px width, the navbar collapses into a toggleable menu.

#### 3.9 Skeleton loader states
**File:** `frontend/src/App.vue` (or a new component), `frontend/src/views/*.vue`
**Problem:** Every view shows only a text spinner ("Ładowanie...").
**Fix:** Create a `SkeletonCard` component using DaisyUI skeleton classes. Use it in `HomeView` (grid of skeletons) and `BookDetailView` (two-column layout skeleton).
**Acceptance:** During loading, the layout roughly matches the final shape, reducing layout shift.

## Reference

- Related audit doc: This spec was derived from the frontend audit performed on 2026-05-11.
- Backend contract: All endpoints verified in `backend-django/`. See audit notes for serializer shapes.
- Next step: Invoke the `writing-plans` skill to break this design into an implementation plan.
