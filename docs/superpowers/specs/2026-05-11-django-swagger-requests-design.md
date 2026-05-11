# Design: Django Swagger Request Examples

## Summary

This document defines a Postman-style Swagger UI reference for Django endpoints in `backend-django/`. It groups requests by Django app so each endpoint has a copy-paste-ready request body or parameter set and a clear expected response.

**Attention Conservation Notice**
For: Engineers testing Django APIs manually
What: Swagger UI request examples grouped by Django app, with expected status codes and responses
Action: Review the endpoint groups and confirm the expected responses match your test needs
Skip if: You only need the API schema and do not test endpoints by hand

## Goal

Create a single Markdown document that shows how to test Django endpoints from Swagger UI. Each entry should tell the reader exactly what to enter, what status code to expect, and what the response should look like.

## Scope

The document covers all Django routes exposed under `backend-django/config/urls.py`:
- `admin/`
- `api/auth/`
- `api/users/`
- `api/books/`
- `api/shelf/`
- `api/authors/`
- `api/series/`
- `api/reviews/`
- `api/internal/`
- `api/schema/`
- `api/docs/`

It does not add new endpoints or change backend behavior.

## Proposed Structure

### 1. Overview

Short intro explaining that the file is a manual testing guide for Swagger UI.

### 2. Auth

Requests for login, logout, register, and `me`.

### 3. Users

Requests for user profile, settings, visibility, follow and unfollow, and follower/following lists.

### 4. Books

Requests for book list, detail, create, chapter upload, chapter list, character list, and relation list.

### 5. Shelf

Requests for shelf list and shelf entry add/remove.

### 6. Authors

Requests for author list and author detail.

### 7. Series

Requests for series list and series detail.

### 8. Reviews

Requests for review list/create/delete if exposed by the current views.

### 9. Internal

Requests for `api/internal/` analysis callbacks.

### 10. Admin, Schema, Docs

Requests for `admin/`, `api/schema/`, and `api/docs/`.

These routes are included for completeness, but `admin/` and `api/docs/` are browser-first routes rather than normal Swagger request bodies.

## Entry Format

Each endpoint entry will use this format:

```markdown
### `METHOD /path/`

**Swagger UI input**

```json
{ "example": "payload" }
```

**Expected result**

- Status: `200 OK`
- Response: short example or note that the body is empty

**Notes**

- Auth: required / not required
- Role: any special permission needed
- Validation: any path/body mismatch rules
```

## Response Rules

- Use the actual status codes returned by the views, not generic guesses.
- Show `204 No Content` when the view returns an empty body.
- Show `401`, `403`, `404`, `409`, or `422` only when the code path clearly returns them.
- If a response body is predictable, include a short example.
- If the response body is not important for manual testing, say so.

## Source Mapping

The document should be derived from these files:
- `backend-django/config/urls.py`
- `backend-django/users/urls/auth.py`
- `backend-django/users/urls/users.py`
- `backend-django/books/urls.py`
- `backend-django/shelf/urls.py`
- `backend-django/library/urls/authors.py`
- `backend-django/library/urls/series.py`
- `backend-django/reviews/urls.py`
- `backend-django/analysis/urls.py`

## Open Questions

None.
