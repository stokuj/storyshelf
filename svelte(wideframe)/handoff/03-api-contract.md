# 03 · API contract

> Fill in the actual paths, headers, and example payloads from your backend before
> handing this to claude-cli. Below is the **expected shape** assuming a REST API.
> If your backend is GraphQL or tRPC, adjust §wrappers but keep §types as-is.

## Base

- `PUBLIC_API_URL` (env) — e.g. `https://api.storyshelf.app`
- Auth: HTTP-only cookie (`storyshelf_session`). Forwarded by `hooks.server.ts`.
- All responses: `application/json`. Errors: `{ "error": { "code": string, "message": string, "fields"?: {} } }`.
- Pagination: `?page=1&per_page=20` → `{ data, page, per_page, total }`.

## Endpoints

### Books

| Method | Path | Returns |
|---|---|---|
| GET | `/books?q=&genre=&sort=&page=` | `Paginated<Book>` |
| GET | `/books/contains-character?name=` | `Paginated<Book>` — for the "contains character" AI filter |
| GET | `/books/:idOrSlug` | `Book` |
| GET | `/books/:idOrSlug/reviews?page=` | `Paginated<Review>` |
| POST | `/books/:id/reviews` | `Review` |

### Characters

| Method | Path | Returns |
|---|---|---|
| GET | `/books/:id/characters` | `Character[]` |
| GET | `/books/:id/relations` | `Relation[]` |
| GET | `/characters/:idOrSlug` | `Character` (cross-book) |
| GET | `/characters/:id/appearances` | `Book[]` |
| PATCH | `/characters/:id` | `Character` — for human edits / verifying AI |

### AI

| Method | Path | Returns |
|---|---|---|
| POST | `/books/:id/ai/extract` | `AIExtraction` — kicks off or returns cached |
| GET  | `/books/:id/ai/extraction` | `AIExtraction` |
| POST | `/books/:id/ai/extract/refresh` | `AIExtraction` — force re-run |
| POST | `/books/:id/ai/extraction/:characterId/verify` | `Character` |
| POST | `/books/:id/ai/extraction/:relationId/verify` | `Relation` |
| POST | `/books/:id/ai/extraction/:characterId/reject` | `{}` |
| POST | `/books/:id/ai/ask` (streamed) | SSE stream — chat answer with citations |

For streaming endpoints use **SSE** (server-sent events). Wrap with EventSource.

### User & social

| Method | Path | Returns |
|---|---|---|
| GET | `/users/me` | `User & { settings: UserSettings }` |
| PATCH | `/users/me` | `User` — display_name, handle, bio |
| PATCH | `/users/me/email` | `{}` — sends verification email |
| PATCH | `/users/me/password` | `{}` |
| PATCH | `/users/me/avatar` | `{ avatar_url }` — multipart upload |
| PATCH | `/users/me/settings` | `UserSettings` |
| POST | `/users/me/export` | `{ download_url }` |
| DELETE | `/users/me` | `{}` |
| GET | `/u/:handle` | `User` (respects visibility) |
| GET | `/u/:handle/shelves` | `Shelf[]` |
| GET | `/u/:handle/activity` | `Paginated<ActivityItem>` |
| POST | `/u/:handle/follow` | `{}` |

### Shelves

| Method | Path | Returns |
|---|---|---|
| GET | `/me/shelves` | `Shelf[]` |
| POST | `/me/shelves/:shelfId/books/:bookId` | `{}` |
| DELETE | `/me/shelves/:shelfId/books/:bookId` | `{}` |

## Wrappers — `src/lib/api/`

One file per resource. Pattern:

```ts
// src/lib/api/books.ts
import type { Book, Paginated } from '$lib/types';
import { apiFetch } from './_client';

export interface ListBooksParams {
  q?: string;
  genre?: string;
  sort?: 'rating' | 'recent' | 'popular';
  page?: number;
}

export async function listBooks(
  fetch: typeof globalThis.fetch,
  params: ListBooksParams = {}
): Promise<Paginated<Book>> {
  return apiFetch(fetch, '/books', { params });
}

export async function getBook(fetch: typeof globalThis.fetch, idOrSlug: string): Promise<Book> {
  return apiFetch(fetch, `/books/${idOrSlug}`);
}
```

```ts
// src/lib/api/_client.ts
import { PUBLIC_API_URL } from '$env/static/public';
import { error } from '@sveltejs/kit';

export async function apiFetch<T>(
  fetch: typeof globalThis.fetch,
  path: string,
  opts: { method?: string; body?: unknown; params?: Record<string, unknown> } = {}
): Promise<T> {
  const url = new URL(PUBLIC_API_URL + path);
  if (opts.params) {
    for (const [k, v] of Object.entries(opts.params)) {
      if (v != null && v !== '') url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url, {
    method: opts.method ?? 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: opts.body ? JSON.stringify(opts.body) : undefined
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw error(res.status, data?.error?.message ?? res.statusText);
  }
  return res.json() as Promise<T>;
}
```

**Always** pass the `event.fetch` from a `load` function — this lets SvelteKit reuse
hydration data and serve cookies correctly.
