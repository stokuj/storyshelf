---
title: Auth Flow
last_updated: 2026-05-22
last_verified_commit: 86ea9b0
owns:
  - backend-django/users/cookie_auth.py
  - backend-django/users/views.py
  - backend-django/users/serializers.py
  - frontend/src/auth.js
  - frontend/src/api.js
depends_on:
  - djangorestframework-simplejwt
related_pages: [api-conventions, dev-setup]
status: stable
---

## Co to jest

Uwierzytelnianie JWT z tokenami w HttpOnly cookies (zamiast localStorage). Backend ustawia
`access_token` i `refresh_token` ciasteczka, frontend nigdy ich nie dotyka. Wszystkie fetche
używają `credentials: 'include'`.

## Jak działa

```
[POST /api/users/login/]
    Django: validate credentials
    → set_jwt_cookies(response, access, refresh)
    → access_token   (HttpOnly, SameSite=Lax, ~15 min)
    → refresh_token  (HttpOnly, SameSite=Lax, path=/api/users/token/refresh/, ~7 dni)
    Response: 200 + user payload

[GET /api/books/]  (z frontu, credentials: 'include')
    Browser → cookies header
    Django: JWTCookieAuthentication.authenticate(request)
        → odczyt access_token z request.COOKIES
        → fallback: Authorization: Bearer (Swagger, CLI)
    → 200 + dane

[401 Unauthorized w api.js]
    api.js: silent retry
    → POST /api/users/token/refresh/  (refresh_token cookie wysyłane automatycznie)
    → backend wystawia nowy access_token cookie
    → ponowienie oryginalnego fetcha
    Jeśli refresh też 401 → signOut() + redirect /login
```

`authState` w `frontend/src/auth.js` to reactive singleton z polami `user`, `authenticated`,
`initialized`. `router.beforeEach` wywołuje `refreshAuth()` jeśli `!initialized` — zapewnia,
że F5 na trasie `requiresAuth` najpierw sprawdza cookie zanim guard odrzuci.

## Decyzje

- Dlaczego HttpOnly cookies a nie localStorage: patrz [ADR-001](../decisions/ADR-001-jwt-httponly-cookies.md)
- Dlaczego osobny refresh cookie z `path=/api/users/token/refresh/`: ogranicza wysyłkę refresh
  tokena tylko do endpointu refresh, zmniejsza powierzchnię ewentualnego CSRF

## Typowe operacje

**Dodanie nowego endpointa wymagającego auth:**
```python
# backend-django/<app>/views.py
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

class MyView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    # authentication_classes — JWTCookieAuthentication jest globalnie w settings
```

**Test auth w shell:**
```bash
# Login → cookies w pliku
curl -c cookies.txt -X POST http://localhost:8000/api/users/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"a@b.c","password":"x"}'

# Użycie zapisanych cookies
curl -b cookies.txt http://localhost:8000/api/books/
```

**Logout w komponencie Vue:**
```javascript
import { signOut } from '@/auth'
await signOut()  // → POST /api/users/logout/ → clear_jwt_cookies()
```

## Pułapki

- **Nie dodawaj localStorage token storage.** Migracja świeża (commits `992ce90..429e1a7`),
  łatwo wrócić do starego nawyku. CLAUDE.md ma to jako twardą regułę.
- **`credentials: 'include'` na każdym fetchu** — bez tego cookies nie idą, otrzymasz 401 mimo
  zalogowania. `api.js#request()` ustawia to domyślnie, ale przy własnych fetchach pamiętaj.
- **CSRF**: `SameSite=Lax` chroni przed cross-site, ale dla endpointów mutujących (POST/PUT/DELETE)
  DRF i tak wymaga CSRF token — wystawiany przez Django automatycznie.
- **Router init**: `beforeEach` musi `await refreshAuth()`, inaczej guard odrzuci usera mimo
  ważnego cookie (race między ładowaniem routera a inicjalizacją authState).
- **Swagger**: używa Bearer header, nie cookies. `JWTCookieAuthentication` ma fallback do
  `Authorization: Bearer` — bez fallbacku Swagger by się zepsuł.

## Pytania, na które ta strona odpowiada

- Jak działa logowanie w StoryShelf?
- Gdzie są przechowywane tokeny JWT?
- Czemu nie używamy localStorage do tokenów?
- Jak dodać nowy endpoint wymagający uwierzytelnienia?
- Co się dzieje, gdy access token wygasa?
- Jak zalogować się z curl/CLI?
- Czemu F5 nie wylogowuje użytkownika?
- Co robi `credentials: 'include'`?
- Czemu Swagger nadal działa, mimo że frontend nie używa headerów?
