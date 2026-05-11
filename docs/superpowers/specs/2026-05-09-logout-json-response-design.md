# Fix: Logout endpoint returns JSON instead of redirect

**Issue:** [#6 — P1: Implement or remove POST /api/auth/logout endpoint](https://github.com/stokuj/storyshelf/issues/6)  
**Date:** 2026-05-09  
**Status:** Approved

## Problem

`api_endpoints.md` documents `POST /api/auth/logout`, but `AuthController.java` has no dedicated logout method. The endpoint **does** work — Spring Security's `LogoutFilter` handles it via `.logoutUrl("/api/auth/logout")` in `SecurityConfig.java`. However, Spring Security's default behavior returns a 302 redirect, which is not idiomatic for a REST API.

## Solution

Add a `LogoutSuccessHandler` in `SecurityConfig.java` that returns `200` with a JSON body, without touching `AuthController`.

## Changes

### 1. `SecurityConfig.java` — Add LogoutSuccessHandler

Add `.logoutSuccessHandler(...)` to the existing `.logout()` configuration block (lines 48–53):

```java
.logout(logout -> logout
        .logoutUrl("/api/auth/logout")
        .logoutSuccessHandler((request, response, authentication) -> {
            response.setStatus(200);
            response.setContentType("application/json");
            response.getWriter().write("{\"message\":\"Logged out successfully\"}");
        })
        .invalidateHttpSession(true)
        .deleteCookies("JSESSIONID")
        .permitAll()
)
```

### 2. `docs/backend/api_endpoints.md` — Update logout row

Change line 12 from:

```
| POST | `/api/auth/logout` | Authenticated | Logout and invalidate session |
```

To:

```
| POST | `/api/auth/logout` | Public | Logout, invalidate session. Returns `200 {"message":"Logged out successfully"}` |
```

Also change the "Access" column for `GET /api/auth/me` from `Public/Auth-aware` to `Public` for consistency (logout requires no auth).

### 3. `AuthControllerTest.java` — Add logout integration test

Two test cases:
- **Authenticated user**: POST `/api/auth/logout` → 200, JSON body, subsequent `/api/auth/me` shows `authenticated=false`
- **Unauthenticated user**: POST `/api/auth/logout` → 200 (idempotent, still works)

## Data flow

```
Frontend: POST /api/auth/logout (credentials: include)
    ↓
Spring Security LogoutFilter:
    1. Invalidates HttpSession
    2. Deletes JSESSIONID cookie
    3. Calls LogoutSuccessHandler → 200 {"message":"Logged out successfully"}
    ↓
Frontend (signOut): resets authState, navigates to /login
```

## Error handling

Logout is `.permitAll()` — no authentication required. Calling logout when not logged in is idempotent (returns 200), which is correct behavior for SPA clients that reset state regardless.

## What is NOT changed

- `AuthController.java` — no new controller method (logout stays in Spring Security filter)
- Frontend (`api.js`, `auth.js`, `App.vue`, `SettingsView.vue`) — no changes needed

## Testing

| Test case | Request | Expected |
|---|---|---|
| Authenticated logout | POST `/api/auth/logout` with session cookie | 200, `{"message":"Logged out successfully"}`, subsequent GET `/api/auth/me` returns `authenticated=false` |
| Unauthenticated logout | POST `/api/auth/logout` without session | 200, `{"message":"Logged out successfully"}` |
