# Frontend Cleanup + Navbar Fix

## Scope

Seven changes across 7 files. Cosmetic cleanup only — no logic changes.

## Changes

### 1. Navbar — "Moja półka" link (App.vue)

Add `<RouterLink to="/bookshelf">Moja półka</RouterLink>` in `navbar-end`, gated behind
`v-if="authState.authenticated"`, before the Profile link.

Navbar layout after login:
```
[Logo]                    [Moja półka] [Profil] [Wyloguj]
```

### 2. Remove dead API functions (api.js)

Delete 12 unused exported functions (never imported by any view/component):

- `fetchAuthors`
- `fetchSeries`
- `fetchBookshelfEntry`
- `createModeratorBook`, `patchModeratorBook`, `deleteModeratorBook`
- `uploadModeratorBookContent`, `clearModeratorBookContent`
- `deleteModeratorReview`
- `createModeratorAuthor`, `updateModeratorAuthor`, `deleteModeratorAuthor`
- `createModeratorSeries`, `updateModeratorSeries`, `deleteModeratorSeries`

Functions confirmed alive and kept: `createBookReview` (used in BookDetailView),
`updateCurrentUserVisibility` (used in SettingsView).

### 3. Delete dead file (mock-data.js)

`frontend/src/mock-data.js` — never imported. Remove entirely.

### 4. Dynamic genre badge (HomeView.vue)

Replace hardcoded `<div class="badge">Vue</div>` with dynamic first genre:
`<div v-if="book.genres?.length">{{ book.genres[0] }}</div>`. Hide badge when
genres array is empty.

### 5. LoginView `?next=` — keep

Functional, just no callers yet. Will be used when auth guards are added to
protected routes. Do not remove.

### 6. Catch-all 404 route

- New `NotFoundView.vue` component: heading "Nie znaleziono" + link to `/`.
- Route `{ path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView }`
  at end of `routes` array.

### 7. Name fix

| File | Before | After |
|---|---|---|
| `App.vue:5` | `SpringShelf` | `StoryShelf` |
| `index.html:6` | `<title>SpringShelf Frontend</title>` | `<title>StoryShelf</title>` |

## Files affected

| File | Action |
|---|---|
| `frontend/src/App.vue` | Add bookshelf link + fix name |
| `frontend/src/api.js` | Remove 12 dead functions |
| `frontend/src/mock-data.js` | Delete |
| `frontend/src/views/HomeView.vue` | Dynamic badge |
| `frontend/src/router.js` | Add catch-all route |
| `frontend/src/views/NotFoundView.vue` | New file |
| `frontend/index.html` | Fix title |

## Verification

```bash
cd frontend && npm run build
```

Build must succeed with no errors.
