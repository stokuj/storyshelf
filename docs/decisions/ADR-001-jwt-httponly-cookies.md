# ADR-001: JWT przez HttpOnly cookies (zamiast localStorage)

**Status:** Zaakceptowane
**Data:** 2026-05-14
**Supersedes:** brak

## Kontekst

Aplikacja używa JWT do uwierzytelniania SPA Vue 3 ↔ Django REST API. Pierwotna implementacja
trzymała tokeny w `localStorage` po stronie frontu. Frontend audit (2026-05-14) zidentyfikował
to jako wektor XSS — każdy skrypt wykonujący się w domenie aplikacji ma dostęp do localStorage,
co przy udanym XSS oznacza kradzież tokenów i pełną reprezentację użytkownika.

## Opcje rozważone

1. **localStorage** (stan przed migracją) — najprostsze, ale XSS-vulnerable
2. **sessionStorage** — to samo ryzyko XSS, dodatkowo F5 może wylogować w niektórych scenariuszach
3. **HttpOnly cookies** — niedostępne dla JavaScript, wymagają CSRF protection
4. **Memory only (reactive singleton)** — najbezpieczniejsze, ale F5 = logout (refresh token i tak musi być persisted gdzieś)

## Decyzja

HttpOnly cookies ustawiane przez backend funkcją `set_jwt_cookies()`. Frontend **nigdy** nie
dotyka tokenów — wszystkie fetche używają `credentials: 'include'`. Header `Authorization: Bearer`
zachowany jako fallback dla Swagger UI i narzędzi CLI (curl, httpie).

Atrybuty cookies:
- `access_token`: `HttpOnly`, `SameSite=Lax`, expire ~15 min
- `refresh_token`: `HttpOnly`, `SameSite=Lax`, `path=/api/users/token/refresh/`, expire ~7 dni

Klasa `JWTCookieAuthentication` (`backend-django/users/cookie_auth.py`) próbuje najpierw
odczytać access token z `request.COOKIES`, potem z headera Authorization (fallback).

## Konsekwencje

- Frontend `api.js` uprasza się — bez ręcznego dodawania headerów
- Silent refresh działa transparentnie: 401 → `POST /api/users/token/refresh/` → backend
  wystawia nowe ciasteczko → ponowienie oryginalnego fetcha
- CSRF: `SameSite=Lax` chroni przed cross-site requests, dla endpointów mutujących Django
  domyślnie wymaga CSRF token (cookie + header)
- **Twarda reguła w CLAUDE.md**: nie dodawaj localStorage token storage nigdzie poza ewentualnym
  jednorazowym migration shim (już niepotrzebny)
- Refresh token w osobnym cookie z `path=` ogranicza wysyłkę tylko do endpointu refresh
- Logout: `clear_jwt_cookies()` ustawia wygasające cookies (`Max-Age=0`)

## SvelteKit SSR note (Phase 2.6)

SvelteKit `hooks.server.ts` forwards the browser's `cookie` header to the Django API via `event.fetch`. This is **cookie passthrough**, not a second session layer. The refresh token stored in HttpOnly cookie is forwarded unchanged — Django handles token validation and silent refresh exactly as in ADR-001. SvelteKit has no knowledge of JWT internals.

## Linki

- Commits: `992ce90`, `2b32ff3`, `0432ef2`, `9028719`, `429e1a7`
- Kod: `backend-django/users/cookie_auth.py`, `backend-django/users/views.py`, `svelte-frontend/src/hooks.server.ts`
