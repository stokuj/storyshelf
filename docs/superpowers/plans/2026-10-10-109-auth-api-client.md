# SPA Auth and API Client Implementation Plan (#109)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The SPA logs in and registers against the real Django backend, keeps the session across reloads, refreshes an expired access token transparently, and redirects logged-out users from wiki routes to `/login`. Wiki data stays on the fake store (#110).

**Architecture:** `src/api/client.ts` is one `fetch` wrapper: same-origin `/api`, cookies included, `ApiError` on non-2xx, and on 401 one shared (single-flight) `POST /api/auth/refresh/` followed by one retry. `src/api/auth.ts` holds `meQuery` and the login/register/logout mutations. The router gets `queryClient` in its context; a pathless layout route `_app` checks `meQuery` in `beforeLoad` and throws a redirect to `/login?redirect=…`. All wiki routes move under `_app/`; `/login` and `/register` sit outside it.

**Tech Stack:** React 19, TanStack Router (file routes, `createRootRouteWithContext`, `beforeLoad` + `redirect`) + Query v5 (`queryOptions`, `ensureQueryData`), Tailwind v4, Vitest + Testing Library (no jest-dom; globals on).

**Spec:** `docs/superpowers/specs/2026-10-10-109-auth-api-client.md`

## Global Constraints

- No new dependencies
- No `localStorage` / `sessionStorage` anywhere (ADR-001)
- Every request: `fetch('/api' + path, { credentials: 'include' })`; `Content-Type: application/json` only when there is a body
- Refresh is never attempted for paths starting with `/auth/`
- `?redirect=` is used only when it starts with `/` and its second character is neither `/` nor `\`; otherwise `/`
- Backend endpoints (unchanged): `POST /api/auth/login/` `{email, password}`, `POST /api/auth/register/` `{email, handle, password}` (both 200/201 + cookies), `POST /api/auth/refresh/`, `POST /api/auth/logout/`, `GET /api/users/me/`
- UI copy, verbatim: `Log in`, `Create account`, `Email`, `Password`, `Handle`, `Lowercase letters, 3–30.`, `No account? Create one`, `Have an account? Log in`, `Log out`, `Something went wrong. Try again.`
- Sidebar `@handle` comes from `useMe`; `/profile` page stays on the fake store (#112)
- All commands run from `frontend/`; `make verify` from the worktree root before PR
- Commit titles ≤ 50 chars, conventional commits, no `Co-Authored-By`; one simple git command per call (worktree guard)

## Review Focus

1. Two requests hit 401 at the same moment → exactly one refresh call, both retried (rotating refresh tokens would otherwise log the user out) — test in Task 1
2. `?redirect=//evil.com`, `https://evil.com` or `/\evil.com` → login lands on `/`, never off-site — test in Task 3
3. Wrong password (400 `non_field_errors`) and throttling (429 `detail`) show a message, not a silent no-op — test in Task 3
4. Logout clears cached data of the previous User (a second login must not see the old `me`) — `queryClient.clear()` + `removeQueries(['me'])` on login, test in Task 4
5. Non-401 error from `/users/me/` (e.g. 500) is not turned into a login redirect — test in Task 2

---

### Task 0: Worktree setup

- [ ] **Step 1: Install dependencies**

Run: `npm ci`
Expected: completes without errors

- [ ] **Step 2: Baseline**

Run: `npm run test`
Expected: all existing tests PASS (note the count; it must not drop)

---

### Task 1: API client with single-flight refresh

**Files:**
- Create: `frontend/src/api/client.ts`
- Test: `frontend/src/api/client.test.ts`

**Interfaces:**
- Produces: `class ApiError extends Error { status: number; body: unknown }`, `api<T>(path: string, init?: RequestInit): Promise<T>` (`path` without the `/api` prefix, e.g. `/users/me/`)

- [ ] **Step 1: Write the failing tests**

`frontend/src/api/client.test.ts`:

```ts
import { ApiError, api } from './client'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

// Access token is "expired" until the refresh endpoint has been called
function stubServer({ refreshOk = true } = {}) {
  let refreshed = false
  const fetchMock = vi.fn(async (url: string) => {
    if (url === '/api/auth/refresh/') {
      refreshed = refreshOk
      return refreshOk ? json(200, { authenticated: true }) : json(401, { detail: 'expired' })
    }
    return refreshed ? json(200, { url }) : json(401, { detail: 'expired' })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const refreshCalls = (f: ReturnType<typeof stubServer>) =>
  f.mock.calls.filter(([url]) => url === '/api/auth/refresh/').length

test('sends same-origin requests with cookies and a JSON body', async () => {
  const f = vi.fn(async () => json(201, { ok: true }))
  vi.stubGlobal('fetch', f)
  await api('/auth/login/', { method: 'POST', body: JSON.stringify({ a: 1 }) })
  expect(f).toHaveBeenCalledWith('/api/auth/login/', {
    method: 'POST',
    body: '{"a":1}',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  })
})

test('401 refreshes once and retries the original request', async () => {
  const f = stubServer()
  expect(await api('/users/me/')).toEqual({ url: '/api/users/me/' })
  expect(refreshCalls(f)).toBe(1)
  expect(f).toHaveBeenCalledTimes(3)
})

test('failed refresh throws ApiError 401', async () => {
  const f = stubServer({ refreshOk: false })
  const err = await api('/users/me/').catch((e: unknown) => e)
  expect(err).toBeInstanceOf(ApiError)
  expect((err as ApiError).status).toBe(401)
  expect(refreshCalls(f)).toBe(1)
})

test('parallel 401s share one refresh', async () => {
  const f = stubServer()
  await Promise.all([api('/a/'), api('/b/')])
  expect(refreshCalls(f)).toBe(1)
})

test('401 on an auth endpoint does not refresh', async () => {
  const f = stubServer()
  await expect(api('/auth/login/', { method: 'POST', body: '{}' })).rejects.toBeInstanceOf(ApiError)
  expect(refreshCalls(f)).toBe(0)
})

test('error body is parsed into ApiError.body', async () => {
  vi.stubGlobal('fetch', async () => json(400, { email: ['Enter a valid email address.'] }))
  const err = (await api('/auth/register/', { method: 'POST', body: '{}' }).catch(
    (e: unknown) => e,
  )) as ApiError
  expect(err.status).toBe(400)
  expect(err.body).toEqual({ email: ['Enter a valid email address.'] })
})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npx vitest run src/api/client.test.ts`
Expected: FAIL — `Failed to resolve import "./client"`

- [ ] **Step 3: Write the implementation**

`frontend/src/api/client.ts`:

```ts
// Same-origin JSON client (ADR-002); both JWTs live in HttpOnly cookies (ADR-001)
export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.status = status
    this.body = body
  }
}

const request = (path: string, init: RequestInit) =>
  fetch(`/api${path}`, {
    ...init,
    credentials: 'include',
    headers: init.body ? { 'Content-Type': 'application/json' } : undefined,
  })

// One refresh for every request that got 401 at once: refresh tokens rotate and
// the old one is blacklisted, so a second parallel refresh would log the user out
let refreshing: Promise<boolean> | null = null
function refresh() {
  refreshing ??= request('/auth/refresh/', { method: 'POST' })
    .then((r) => r.ok)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await request(path, init)
  if (res.status === 401 && !path.startsWith('/auth/') && (await refresh())) {
    res = await request(path, init)
  }
  const body: unknown = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, body)
  return body as T
}
```

Note: when there is no body, `headers` is `undefined`; the first test passes a body, so it expects the header. `toHaveBeenCalledWith` for a GET would include `headers: undefined`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npx vitest run src/api/client.test.ts`
Expected: 6 PASS

- [ ] **Step 5: Lint and typecheck**

Run: `npm run typecheck`
Expected: no errors
Run: `npm run lint`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add src/api/client.ts src/api/client.test.ts
```
```bash
git commit -m "feat: add API client with refresh and retry"
```

---

### Task 2: Router context, `_app` guard and current user

**Files:**
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/routes/_app.tsx`
- Create: `frontend/src/test/mockFetch.ts`
- Create: `frontend/src/test/auth.test.tsx`
- Move: `frontend/src/routes/{index,$,add,profile}.tsx` → `frontend/src/routes/_app/`
- Modify: `frontend/src/routes/__root.tsx`, `frontend/src/main.tsx`, `frontend/src/test/renderApp.tsx`, `frontend/src/test/setup.ts`
- Regenerate: `frontend/src/routeTree.gen.ts`

**Interfaces:**
- Consumes: `api`, `ApiError` (Task 1)
- Produces:
  - `auth.ts`: `interface Me { id: number; handle: string; display_name: string; email: string; bio: string; avatar_url: string | null; member_since: string; profile_public: boolean }`, `meQuery` (`queryKey: ['me']`), `useMe(): UseQueryResult<Me>`
  - `mockFetch.ts`: `ME: Me` (handle `stokuj`), `json(status, body): Response`, `mockFetch(routes?: Record<string, (init?: RequestInit) => Response>)` — keys like `'POST /api/auth/login/'`; default route `GET /api/users/me/` → 200 `ME`; unknown → 404; returns the `vi.fn`
  - Router context type `{ queryClient: QueryClient }`; route IDs `/_app`, `/_app/`, `/_app/$`, `/_app/add`, `/_app/profile` (URLs unchanged)
  - Minimal `routes/login.tsx` stub (Step 6): `redirect({ to: '/login' })` needs the route to exist; Task 3 replaces its component

- [ ] **Step 1: Test helper `mockFetch`**

`frontend/src/test/mockFetch.ts`:

```ts
import type { Me } from '@/api/auth'

export const ME: Me = {
  id: 1,
  handle: 'stokuj',
  display_name: '',
  email: 'stokuj@example.com',
  bio: '',
  avatar_url: null,
  member_since: '2026-01-01T00:00:00Z',
  profile_public: true,
}

export const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

type Route = (init?: RequestInit) => Response

// Stubs fetch with 'METHOD /api/path' routes on top of a logged-in User; anything else is 404
export function mockFetch(routes: Record<string, Route> = {}) {
  const all: Record<string, Route> = { 'GET /api/users/me/': () => json(200, ME), ...routes }
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const route = all[`${init?.method ?? 'GET'} ${url}`]
    return route ? route(init) : json(404, { detail: 'Not found.' })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}
```

`frontend/src/test/setup.ts` (add the default logged-in User):

```ts
import { resetStore } from '@/api/store'
import { mockFetch } from './mockFetch'

// The fake store is module state: every test starts from the fixtures
afterEach(resetStore)
// Every test starts logged in; auth tests override routes with mockFetch({...})
beforeEach(() => mockFetch())
```

- [ ] **Step 2: Write the failing guard tests**

`frontend/src/test/auth.test.tsx`:

```tsx
import { screen, waitFor } from '@testing-library/react'
import { json, mockFetch } from './mockFetch'
import { renderApp } from './renderApp'

const loggedOut = {
  'GET /api/users/me/': () => json(401, { detail: 'Authentication credentials were not provided.' }),
  'POST /api/auth/refresh/': () => json(401, { detail: 'Refresh token not found.' }),
}

test('logged-out user on a wiki route is sent to login', async () => {
  mockFetch(loggedOut)
  const router = renderApp('/books/solaris')
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
  expect(router.state.location.search).toEqual({ redirect: '/books/solaris' })
  await screen.findByRole('heading', { name: 'Log in' })
  expect(screen.queryByRole('navigation', { name: 'Wiki' })).toBeNull()
})

test('logged-in user stays on the wiki route', async () => {
  const router = renderApp('/books/solaris')
  await screen.findByRole('heading', { level: 1, name: 'Solaris' })
  expect(router.state.location.pathname).toBe('/books/solaris')
})

test('server error on me is not a login redirect', async () => {
  mockFetch({ 'GET /api/users/me/': () => json(500, null) })
  const router = renderApp('/')
  // Router shows its default error component; the URL stays put
  await screen.findByText(/something went wrong/i)
  expect(router.state.location.pathname).toBe('/')
})
```

- [ ] **Step 3: Run to verify they fail**

Run: `npx vitest run src/test/auth.test.tsx`
Expected: FAIL — `Failed to resolve import "@/api/auth"` (from `mockFetch.ts`)

- [ ] **Step 4: `auth.ts` with `meQuery`**

`frontend/src/api/auth.ts`:

```ts
// Session = HttpOnly cookies (ADR-001); the SPA only knows who is logged in via /users/me/
import { queryOptions, useQuery } from '@tanstack/react-query'
import { api } from './client'

// GET /api/users/me/ (UserMeSerializer)
export interface Me {
  id: number
  handle: string
  display_name: string
  email: string
  bio: string
  avatar_url: string | null
  member_since: string
  profile_public: boolean
}

export const meQuery = queryOptions({
  queryKey: ['me'],
  queryFn: () => api<Me>('/users/me/'),
  // 'me' changes only on login, register and logout, which reset it explicitly
  retry: false,
  staleTime: Infinity,
})

export const useMe = () => useQuery(meQuery)
```

- [ ] **Step 5: Move wiki routes under `_app/`**

Run each (one git command per call):

```bash
mkdir -p src/routes/_app
```
```bash
git mv src/routes/index.tsx src/routes/_app/index.tsx
```
```bash
git mv 'src/routes/$.tsx' 'src/routes/_app/$.tsx'
```
```bash
git mv src/routes/add.tsx src/routes/_app/add.tsx
```
```bash
git mv src/routes/profile.tsx src/routes/_app/profile.tsx
```

Then change only the route ID string in each moved file:

| File | Before | After |
|---|---|---|
| `_app/index.tsx` | `createFileRoute('/')` | `createFileRoute('/_app/')` |
| `_app/$.tsx` | `createFileRoute('/$')` | `createFileRoute('/_app/$')` |
| `_app/add.tsx` | `createFileRoute('/add')` | `createFileRoute('/_app/add')` |
| `_app/profile.tsx` | `createFileRoute('/profile')` | `createFileRoute('/_app/profile')` |

`<Link to="/$">`, `to="/add"`, `to="/profile"` and `navigate({ to: '/$' })` stay as they are (they are URLs, not IDs).

- [ ] **Step 6: Root, `_app` layout, login stub**

`frontend/src/routes/__root.tsx` (whole file):

```tsx
import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

// queryClient in the context lets beforeLoad guards read cached queries
export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: Outlet,
})
```

`frontend/src/routes/_app.tsx`:

```tsx
// Pathless layout for every wiki route: logged-out users go to /login
import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'
import { meQuery } from '@/api/auth'
import { ApiError } from '@/api/client'
import { Sidebar } from '@/components/Sidebar'

export const Route = createFileRoute('/_app')({
  beforeLoad: async ({ context, location }) => {
    try {
      await context.queryClient.ensureQueryData(meQuery)
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        throw redirect({ to: '/login', search: { redirect: location.href } })
      }
      throw e
    }
  },
  component: AppLayout,
})

function AppLayout() {
  return (
    <div className="grid h-svh grid-cols-[16rem_1fr]">
      <Sidebar />
      <main className="overflow-y-auto px-12 py-10">
        <Outlet />
      </main>
    </div>
  )
}
```

`frontend/src/routes/login.tsx` (stub; Task 3 replaces the component):

```tsx
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/login')({
  validateSearch: (s: Record<string, unknown>): { redirect?: string } => ({
    redirect: typeof s.redirect === 'string' ? s.redirect : undefined,
  }),
  component: () => <h1>Log in</h1>,
})
```

- [ ] **Step 7: Router context in `main.tsx` and `renderApp`**

`frontend/src/main.tsx` — change one line:

```tsx
const router = createRouter({ routeTree, context: { queryClient } })
```

`frontend/src/test/renderApp.tsx` (whole file):

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createMemoryHistory, createRouter } from '@tanstack/react-router'
import { render } from '@testing-library/react'
import { routeTree } from '@/routeTree.gen'

// Full app (all file routes) on an in-memory URL
export function renderApp(url = '/') {
  const queryClient = new QueryClient()
  const router = createRouter({
    routeTree,
    context: { queryClient },
    history: createMemoryHistory({ initialEntries: [url] }),
  })
  render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return router
}
```

- [ ] **Step 8: Regenerate the route tree**

Run: `npm run build`
Expected: build succeeds; `git status` shows `src/routeTree.gen.ts` modified with `/_app`, `/login` routes

- [ ] **Step 9: Run the whole suite**

Run: `npm run test`
Expected: all PASS — baseline count + 6 (client) + 3 (auth). If "server error on me" fails on the text, check what TanStack's default `errorComponent` renders (`screen.debug()`) and match that text; do not add a custom error component.

- [ ] **Step 10: Typecheck, lint, format**

Run: `npm run typecheck`
Run: `npm run lint`
Run: `npm run format`
Expected: no errors

- [ ] **Step 11: Commit**

```bash
git add -A src
```
```bash
git commit -m "feat: guard wiki routes with current user"
```

---

### Task 3: Login and register screens

**Files:**
- Create: `frontend/src/components/AuthCard.tsx`
- Create: `frontend/src/routes/register.tsx`
- Modify: `frontend/src/routes/login.tsx` (replace stub), `frontend/src/api/auth.ts`
- Test: `frontend/src/test/auth.test.tsx`
- Regenerate: `frontend/src/routeTree.gen.ts`

**Interfaces:**
- Consumes: `api`, `ApiError` (Task 1); `meQuery`, `mockFetch`, `json`, `ME` (Task 2)
- Produces:
  - `auth.ts`: `safeRedirect(to?: string): string`, `useLogin()` (mutation, variables `{ email: string; password: string }`), `useRegister()` (variables `{ email: string; handle: string; password: string }`)
  - `auth.ts`: `formErrors(error: unknown): Record<string, string>` (key `form` = whole-form message)
  - `AuthCard.tsx` (components only, for `react-refresh/only-export-components`): `AuthCard({ title, error, children })`, `Field({ label, error, hint, ...inputProps })`, `SubmitButton({ pending, children })`

- [ ] **Step 1: Write the failing tests** (append to `src/test/auth.test.tsx`)

Add to the imports at the top: `import { fireEvent, screen, waitFor } from '@testing-library/react'`, `import { safeRedirect } from '@/api/auth'`, and `ME` from `./mockFetch`.

```tsx
const fill = (label: string, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
// Submit the form itself: a submit event on the button does not reach React's onSubmit
const submit = (button: string) =>
  fireEvent.submit(screen.getByRole('button', { name: button }).closest('form')!)

// me is 401 until login/register succeeds
function server(authRoute: string, reply: () => Response) {
  let loggedIn = false
  return mockFetch({
    ...loggedOut,
    'GET /api/users/me/': () => (loggedIn ? json(200, ME) : json(401, { detail: 'no' })),
    [authRoute]: () => {
      const res = reply()
      loggedIn = res.ok
      return res
    },
  })
}

test('login lands on the redirect target and stores nothing in web storage', async () => {
  const f = server('POST /api/auth/login/', () => json(200, { authenticated: true }))
  const router = renderApp('/login?redirect=%2Fbooks%2Fsolaris')
  fill('Email', 'stokuj@example.com')
  fill('Password', 'secret123')
  submit('Log in')
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/solaris'))
  expect(f).toHaveBeenCalledWith(
    '/api/auth/login/',
    expect.objectContaining({ body: '{"email":"stokuj@example.com","password":"secret123"}' }),
  )
  expect(localStorage.length + sessionStorage.length).toBe(0)
})

test('wrong password shows the server message', async () => {
  server('POST /api/auth/login/', () =>
    json(400, { non_field_errors: ['Invalid email or password'] }),
  )
  renderApp('/login')
  fill('Email', 'stokuj@example.com')
  fill('Password', 'wrongpass')
  submit('Log in')
  expect((await screen.findByRole('alert')).textContent).toBe('Invalid email or password')
})

test('throttled login shows the detail message', async () => {
  server('POST /api/auth/login/', () =>
    json(429, { detail: 'Request was throttled. Expected available in 60 seconds.' }),
  )
  renderApp('/login')
  fill('Email', 'stokuj@example.com')
  fill('Password', 'secret123')
  submit('Log in')
  expect((await screen.findByRole('alert')).textContent).toMatch(/throttled/)
})

test('unsafe redirect target falls back to home', async () => {
  server('POST /api/auth/login/', () => json(200, { authenticated: true }))
  const router = renderApp('/login?redirect=%2F%2Fevil.com')
  fill('Email', 'stokuj@example.com')
  fill('Password', 'secret123')
  submit('Log in')
  await waitFor(() => expect(router.state.location.pathname).toBe('/'))
})

test.each([
  [undefined, '/'],
  ['/books/solaris?view=edit', '/books/solaris?view=edit'],
  ['//evil.com', '/'],
  ['/\\evil.com', '/'],
  ['https://evil.com', '/'],
  ['books', '/'],
])('safeRedirect(%s) is %s', (to, expected) => {
  expect(safeRedirect(to)).toBe(expected)
})

test('register shows field errors from the server', async () => {
  server('POST /api/auth/register/', () =>
    json(400, { handle: ['user with this handle already exists.'] }),
  )
  renderApp('/register')
  fill('Email', 'new@example.com')
  fill('Handle', 'stokuj')
  fill('Password', 'secret123')
  submit('Create account')
  await screen.findByText('user with this handle already exists.')
})

test('register logs in and lands on the wiki', async () => {
  server('POST /api/auth/register/', () =>
    json(201, { authenticated: true, email: 'new@example.com', handle: 'nowy' }),
  )
  const router = renderApp('/register')
  fill('Email', 'new@example.com')
  fill('Handle', 'nowy')
  fill('Password', 'secret123')
  submit('Create account')
  await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  await screen.findByRole('navigation', { name: 'Wiki' })
})

test('login and register link to each other', async () => {
  const router = renderApp('/login')
  fireEvent.click(await screen.findByRole('link', { name: 'No account? Create one' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/register'))
  fireEvent.click(await screen.findByRole('link', { name: 'Have an account? Log in' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/auth.test.tsx`
Expected: FAIL — `safeRedirect` is not exported / no `Email` label

- [ ] **Step 3: Mutations and `safeRedirect` in `auth.ts`**

Change the imports and append to `frontend/src/api/auth.ts`:

```ts
import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, api } from './client'
```

```ts
const post = (path: string, data: unknown) =>
  api(path, { method: 'POST', body: JSON.stringify(data) })

// Only paths inside the app: '//evil.com', '/\evil.com' or 'https://…' would leave it
export const safeRedirect = (to?: string) => (to && /^\/(?![/\\])/.test(to) ? to : '/')

export interface Credentials {
  email: string
  password: string
}

// A new session: drop any cached 'me' so the guard fetches the new User
function useSessionMutation<V>(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: V) => post(path, data),
    onSuccess: () => qc.removeQueries({ queryKey: ['me'] }),
  })
}

export const useLogin = () => useSessionMutation<Credentials>('/auth/login/')

// DRF errors: { field: [msg] } per field; non_field_errors / detail belong to the whole form
export function formErrors(error: unknown): Record<string, string> {
  if (!error) return {}
  if (!(error instanceof ApiError) || !error.body || typeof error.body !== 'object') {
    return { form: 'Something went wrong. Try again.' }
  }
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(error.body)) {
    const name = key === 'non_field_errors' || key === 'detail' ? 'form' : key
    out[name] = Array.isArray(value) ? value.join(' ') : String(value)
  }
  return out
}

// The backend sets the session cookies on register too
export const useRegister = () =>
  useSessionMutation<Credentials & { handle: string }>('/auth/register/')
```

- [ ] **Step 4: `AuthCard.tsx`**

`frontend/src/components/AuthCard.tsx`:

```tsx
import type { InputHTMLAttributes, ReactNode } from 'react'

export function AuthCard({
  title,
  error,
  children,
}: {
  title: string
  error?: string
  children: ReactNode
}) {
  return (
    <main className="grid min-h-svh place-items-center bg-sidebar px-4">
      <section className="w-full max-w-sm rounded-lg border bg-background p-8">
        <p className="font-heading text-xl font-semibold">StoryShelf</p>
        <h1 className="mt-6 font-heading text-3xl">{title}</h1>
        {error && (
          <p role="alert" className="mt-4 text-sm text-destructive">
            {error}
          </p>
        )}
        {children}
      </section>
    </main>
  )
}

export function Field({
  label,
  error,
  hint,
  ...input
}: { label: string; error?: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="mt-4 block text-sm font-medium">
      {label}
      <input
        required
        {...input}
        className="mt-1 block w-full rounded-md border bg-background px-3 py-2 font-normal"
      />
      {(error ?? hint) && (
        <span className={`mt-1 block text-xs ${error ? 'text-destructive' : 'text-muted-foreground'}`}>
          {error ?? hint}
        </span>
      )}
    </label>
  )
}

export function SubmitButton({ pending, children }: { pending: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-6 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
    >
      {children}
    </button>
  )
}
```

Note: `getByLabelText('Email')` matches because the label's accessible text is `Email` plus any error/hint span. If Testing Library fails to match with a hint present (`Handle` has one), switch the test to `getByLabelText(/^Handle/)` — do not drop the hint.

- [ ] **Step 5: `login.tsx` (replace stub)**

`frontend/src/routes/login.tsx`:

```tsx
import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import type { FormEvent } from 'react'
import { type Credentials, formErrors, safeRedirect, useLogin } from '@/api/auth'
import { AuthCard, Field, SubmitButton } from '@/components/AuthCard'

export const Route = createFileRoute('/login')({
  validateSearch: (s: Record<string, unknown>): { redirect?: string } => ({
    redirect: typeof s.redirect === 'string' ? s.redirect : undefined,
  }),
  component: LoginPage,
})

function LoginPage() {
  const { redirect } = Route.useSearch()
  const router = useRouter()
  const login = useLogin()
  const errors = formErrors(login.error)

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.currentTarget)) as unknown as Credentials
    // redirect is a full href (path + search), so push it as-is
    login.mutate(data, { onSuccess: () => router.history.push(safeRedirect(redirect)) })
  }

  return (
    <AuthCard title="Log in" error={errors.form}>
      <form onSubmit={submit}>
        <Field label="Email" name="email" type="email" autoComplete="email" error={errors.email} />
        <Field
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          error={errors.password}
        />
        <SubmitButton pending={login.isPending}>Log in</SubmitButton>
      </form>
      <Link to="/register" className="mt-4 block text-center text-sm text-primary">
        No account? Create one
      </Link>
    </AuthCard>
  )
}
```

- [ ] **Step 6: `register.tsx`**

`frontend/src/routes/register.tsx`:

```tsx
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import type { FormEvent } from 'react'
import { type Credentials, formErrors, useRegister } from '@/api/auth'
import { AuthCard, Field, SubmitButton } from '@/components/AuthCard'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const errors = formErrors(register.error)

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.currentTarget)) as unknown as Credentials & {
      handle: string
    }
    register.mutate(data, { onSuccess: () => navigate({ to: '/' }) })
  }

  return (
    <AuthCard title="Create account" error={errors.form}>
      <form onSubmit={submit}>
        <Field label="Email" name="email" type="email" autoComplete="email" error={errors.email} />
        {/* Same rule as RegisterSerializer.handle */}
        <Field
          label="Handle"
          name="handle"
          pattern="[a-z]{3,30}"
          autoComplete="username"
          hint="Lowercase letters, 3–30."
          error={errors.handle}
        />
        <Field
          label="Password"
          name="password"
          type="password"
          minLength={8}
          maxLength={72}
          autoComplete="new-password"
          error={errors.password}
        />
        <SubmitButton pending={register.isPending}>Create account</SubmitButton>
      </form>
      <Link to="/login" className="mt-4 block text-center text-sm text-primary">
        Have an account? Log in
      </Link>
    </AuthCard>
  )
}
```

Note: the title `Create account` and the submit button share the same text; the tests query `getByRole('button', …)`, so there is no clash with the heading.

- [ ] **Step 7: Regenerate the route tree and run the tests**

Run: `npm run build`
Expected: succeeds; `routeTree.gen.ts` now has `/register`
Run: `npx vitest run src/test/auth.test.tsx`
Expected: all PASS
Run: `npm run test`
Expected: all PASS

- [ ] **Step 8: Typecheck, lint, format**

Run: `npm run typecheck`
Run: `npm run lint`
Run: `npm run format`
Expected: no errors

- [ ] **Step 9: Commit**

```bash
git add -A src
```
```bash
git commit -m "feat: add login and register screens"
```

---

### Task 4: Sidebar footer with real handle and logout

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`, `frontend/src/api/auth.ts`
- Test: `frontend/src/test/auth.test.tsx`

**Interfaces:**
- Consumes: `useMe`, `api` (Tasks 1–2), `mockFetch`, `json`, `ME` (Task 2)
- Produces: `useLogout()` (mutation, no variables; on success navigates to `/login` and clears the query cache)

- [ ] **Step 1: Write the failing tests** (append to `src/test/auth.test.tsx`)

Add `within` to the Testing Library import.

```tsx
test('sidebar shows the handle from /users/me/', async () => {
  mockFetch({ 'GET /api/users/me/': () => json(200, { ...ME, handle: 'realuser' }) })
  renderApp('/')
  const nav = await screen.findByRole('navigation', { name: 'Wiki' })
  await within(nav).findByRole('link', { name: '@realuser' })
})

test('log out ends the session and returns to login', async () => {
  let loggedIn = true
  const f = mockFetch({
    ...loggedOut,
    'GET /api/users/me/': () => (loggedIn ? json(200, ME) : json(401, { detail: 'no' })),
    'POST /api/auth/logout/': () => {
      loggedIn = false
      return json(200, { message: 'Logged out successfully' })
    },
  })
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('button', { name: 'Log out' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
  expect(f).toHaveBeenCalledWith('/api/auth/logout/', expect.objectContaining({ method: 'POST' }))
  // Back to the wiki: the old 'me' is gone from the cache, so the guard asks again
  router.history.push('/')
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
})
```

- [ ] **Step 2: Run to verify they fail**

Run: `npx vitest run src/test/auth.test.tsx`
Expected: FAIL — no `@realuser` link, no `Log out` button

- [ ] **Step 3: `useLogout` in `auth.ts`**

Add `import { useNavigate } from '@tanstack/react-router'` at the top, then append:

```ts
export function useLogout() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => api('/auth/logout/', { method: 'POST' }),
    // Leave the wiki first so no mounted query refetches as a logged-out user
    onSuccess: async () => {
      await navigate({ to: '/login' })
      qc.clear()
    },
  })
}
```

If `tsc` demands `search` on `navigate({ to: '/login' })`, pass `search: {}`.

- [ ] **Step 4: Sidebar footer**

In `frontend/src/components/Sidebar.tsx`:

Replace the imports line `import { usePages, useProfile } from '@/api/hooks'` with:

```tsx
import { useLogout, useMe } from '@/api/auth'
import { usePages } from '@/api/hooks'
```

Replace `const { data: profile } = useProfile()` with:

```tsx
  const { data: me } = useMe()
  const logout = useLogout()
```

Replace the whole `{profile && ( <Link to="/profile" …>@{profile.handle}</Link> )}` block with:

```tsx
      {me && (
        <div className="mt-auto flex items-center justify-between gap-2">
          <Link
            to="/profile"
            className="rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-background"
            activeProps={{ className: 'bg-background font-medium text-primary' }}
          >
            @{me.handle}
          </Link>
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-background disabled:opacity-50"
          >
            Log out
          </button>
        </div>
      )}
```

- [ ] **Step 5: Run the tests**

Run: `npm run test`
Expected: all PASS (existing `profile.test.tsx` still finds `@stokuj` because `ME.handle` is `stokuj`)

- [ ] **Step 6: Typecheck, lint, format**

Run: `npm run typecheck`
Run: `npm run lint`
Run: `npm run format`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add -A src
```
```bash
git commit -m "feat: show real handle and log out in sidebar"
```

---

### Task 5: Verify against the real backend

- [ ] **Step 1: Full gate**

Run (worktree root): `make verify`
Expected: ruff, backend tests, frontend typecheck/lint/format/test/build all green; `git diff --exit-code frontend/src/routeTree.gen.ts` clean

- [ ] **Step 2: Live check (Done when 1–4)**

1. `make dev-up` (worktree root); then `npm run dev` in `frontend/`
2. Open `http://localhost:5173/books/solaris` logged out → lands on `/login?redirect=%2Fbooks%2Fsolaris`
3. `Create one` → register a new user → lands on `/`, sidebar shows `@<handle>`
4. Reload → still logged in
5. DevTools → Application: `access_token` / `refresh_token` cookies are HttpOnly; Local/Session Storage empty
6. `Log out` → `/login`; `/` redirects to login again; log back in → lands on `/`
7. Optional refresh check: set `JWT_ACCESS_TOKEN_LIFETIME` short (or delete the `access_token` cookie in DevTools), reload → still logged in, Network shows `refresh/` then `me/` retried

Register throttle is 5/hour on the live server (`docs/GOTCHAS.md`); raise `THROTTLE_AUTH_REGISTER` if you hit 429.

- [ ] **Step 3: Commit only if something changed** (e.g. a fix found in the live check), with a `fix:` title ≤ 50 chars.
