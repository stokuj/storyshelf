# Spec — Logowanie, rejestracja i klient API w SPA (#109)

> Data: 2026-10-10 · Issue: #109 · Milestone: M2 · Decyzje: ADR-001 (JWT w HttpOnly cookies), ADR-002 (same-origin API), ADR-005 · Backend: `backend-django/users/urls/auth.py`, `users/views.py`, `users/cookie_auth.py` · Wzorzec: TanStack Router „Authenticated Routes” (pathless layout + `beforeLoad`)

## Cel

User rejestruje się albo loguje w SPA na prawdziwym backendzie i ląduje na Wiki. Reload zachowuje sesję. Wygasły access token odświeża się sam, a pierwotne żądanie przechodzi. Niezalogowany User na trasie Wiki trafia na `/login`. Wiki dalej działa na fake store (prawdziwe API Stron to #110).

## Decyzje

| Temat | Decyzja | Powód |
|---|---|---|
| Klient HTTP | własna funkcja `api<T>(path, init?)` na `fetch`, bez axios/ky | ~40 linii, bez nowej zależności |
| Żądanie | `fetch('/api' + path, { credentials: 'include' })`, `Content-Type: application/json` przy body, odpowiedź jako JSON (204 → `undefined`) | ADR-002 same-origin; `include` zgodnie z issue |
| Błąd | `ApiError extends Error { status, body }`, `body` to sparsowany JSON DRF (albo `null`) | formularze czytają błędy pól z `body` |
| 401 | dla ścieżek spoza `/auth/`: jeden `POST /api/auth/refresh/`, potem jedna ponowna próba; refresh nieudany → `ApiError(401)` | Done when 2; `/auth/*` bez refresh, żeby nie zapętlić |
| Równoległe 401 | single-flight: jedna wspólna obietnica refresh, zerowana po zakończeniu | backend ma `ROTATE_REFRESH_TOKENS=True` + blacklist; dwa równoległe refresh = drugi z unieważnionym tokenem = wylogowanie |
| Bieżący User | `meQuery = queryOptions({ queryKey: ['me'], queryFn: GET /users/me/, retry: false, staleTime: Infinity })` + `useMe()` | Done when 1; sesja to cookie, `me` zmienia się tylko przy login/logout |
| Login / rejestracja | mutacje `useLogin`, `useRegister`; po sukcesie `invalidateQueries(['me'])`, potem nawigacja na `redirect` albo `/` | backend przy rejestracji od razu ustawia cookies, więc po rejestracji User jest zalogowany |
| Wylogowanie | `useLogout`: `POST /auth/logout/`, `queryClient.clear()`, nawigacja na `/login` | czyści cache poprzedniego Usera |
| Guard | pathless layout `_app.tsx`: `beforeLoad` → `context.queryClient.ensureQueryData(meQuery)`; `ApiError` 401 → `throw redirect({ to: '/login', search: { redirect: location.href } })`; inne błędy przepuszcza | wzorzec TanStack; brak mignięcia Wiki przed przekierowaniem |
| Kontekst routera | `__root.tsx` → `createRootRouteWithContext<{ queryClient: QueryClient }>()`, sam `<Outlet/>`; `main.tsx` przekazuje `context: { queryClient }` | `beforeLoad` potrzebuje QueryClient |
| Trasy | `index`, `$`, `add`, `profile` przeniesione do `routes/_app/`; `login.tsx`, `register.tsx` poza layoutem; `routeTree.gen.ts` zacommitowany | logowanie bez panelu bocznego; CI sprawdza `routeTree.gen.ts` |
| `?redirect` | `validateSearch` przyjmuje string; użyty tylko gdy zaczyna się od `/` i nie od `//`, inaczej `/` | blokuje open redirect |
| Wygląd | wyśrodkowana karta w obecnym stylu (nagłówek Newsreader, kolory i inputy jak w aplikacji), bez nowej makiety | decyzja Usera; brak makiety logowania w `docs/mockups/` |
| Walidacja | natywna HTML: `type=email`, `required`, hasło `minLength=8`, handle `pattern="[a-z]{3,30}"` | zgodne z `RegisterSerializer`; backend i tak waliduje |
| Błędy formularza | błędy pól DRF pod polami; `non_field_errors` / `detail` nad formularzem z `role="alert"`; przycisk `disabled` w trakcie | DRF zwraca `{ pole: [..] }` lub `{ non_field_errors: [..] }` |
| Pola rejestracji | email, handle, hasło; bez `display_name` | `display_name` opcjonalne w backendzie |
| Linki | login ↔ rejestracja wzajemnie | — |
| Panel boczny | stopka: `@handle` z `useMe` (link do `/profile`) + przycisk „Log out”; `useProfile` znika z Sidebar | decyzja Usera; strona `/profile` zostaje na fake store do #112 |
| Storage | zero `localStorage` / `sessionStorage` | ADR-001, Done when 4 |

## Pliki

```
frontend/src/
  api/client.ts                nowy: api(), ApiError, single-flight refresh
  api/client.test.ts           nowy: refresh-and-retry, refresh fail, równoległe 401, /auth/ bez refresh
  api/auth.ts                  nowy: Me, meQuery, useMe, useLogin, useRegister, useLogout
  main.tsx                     context: { queryClient }
  routes/__root.tsx            createRootRouteWithContext, sam Outlet
  routes/_app.tsx              nowy: beforeLoad guard + Sidebar + Outlet
  routes/_app/index.tsx        przeniesiony
  routes/_app/$.tsx            przeniesiony
  routes/_app/add.tsx          przeniesiony
  routes/_app/profile.tsx      przeniesiony
  routes/login.tsx             nowy
  routes/register.tsx          nowy
  routeTree.gen.ts             wygenerowany
  components/Sidebar.tsx       stopka: useMe + Log out
  test/renderApp.tsx           QueryClient w kontekście routera + mock /api/users/me/
  test/auth.test.tsx           nowy: guard, login, rejestracja, wylogowanie
```

## Testy

- `client.test.ts` (mock `fetch`): 401 → refresh 200 → ponowna próba 200; refresh 401 → `ApiError(401)`; dwa równoległe 401 → dokładnie jedno wywołanie refresh; 401 na `/auth/login/` → bez refresh.
- `auth.test.tsx`: `me` 401 na `/` → URL `/login?redirect=...`; login → `/` (albo `redirect`); błąd 400 → komunikat w `role="alert"`; rejestracja → `/`; „Log out” → `/login`.
- `renderApp` domyślnie mockuje zalogowanego Usera, więc istniejące testy działają bez zmian w treści.
- Ręcznie: `make dev-up` + `npm run dev`: rejestracja → reload (sesja zostaje) → wylogowanie → `/` przekierowuje na `/login`.

## Done when (z issue)

1. Rejestracja, potem logowanie, kończy się na Wiki; reload zachowuje sesję.
2. Wygasły access token: klient odświeża i pierwotne żądanie przechodzi.
3. Niezalogowany User na trasie Wiki trafia na login.
4. Brak tokenu w `localStorage` i `sessionStorage`.
5. Vitest pokrywa refresh-and-retry z zamockowanym `fetch`; CI zielone.

## Poza zakresem

Ekrany Wiki na prawdziwym API (#110), prawdziwy Profil (#112), reset hasła, zmiana emaila, avatar, `display_name`, ukrywanie `/login` dla zalogowanego, „zapamiętaj mnie”.
