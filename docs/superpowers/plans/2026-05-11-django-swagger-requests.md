# Django Swagger Request Examples Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a Markdown reference with copy-paste-ready Swagger UI request examples for every Django endpoint group, plus expected status codes and response shapes.

**Architecture:** One document under `docs/backend/` with sections grouped by Django app and route prefix. Each endpoint entry will show the exact Swagger UI input, the expected HTTP status, and a short response note so manual testing stays fast and consistent.

**Tech Stack:** Markdown documentation, Django URL/view inspection, Swagger UI manual testing

---

### Task 1: Map endpoint groups and file structure

**Files:**
- Create: `docs/backend/swagger_requests.md`
- Reference: `backend-django/config/urls.py`
- Reference: `backend-django/users/urls/auth.py`
- Reference: `backend-django/users/urls/users.py`
- Reference: `backend-django/books/urls.py`
- Reference: `backend-django/shelf/urls.py`
- Reference: `backend-django/library/urls/authors.py`
- Reference: `backend-django/library/urls/series.py`
- Reference: `backend-django/reviews/urls.py`
- Reference: `backend-django/analysis/urls.py`

- [ ] **Step 1: Write the file skeleton and section headings**

```markdown
# Django Swagger Request Examples

This guide collects Swagger UI examples for Django endpoints in `backend-django/`.
Use it when you want to paste request data into Swagger UI and confirm the expected response.

Attention Conservation Notice
For: Engineers testing Django APIs manually
What: Copy-paste Swagger UI request examples grouped by Django app, with expected responses
Action: Use the section for the app you are testing and match the expected status code
Skip if: You only need the schema and do not test endpoints by hand

## Before You Start

- Open Swagger UI at `/api/docs/`
- Authenticate first if the endpoint requires `IsAuthenticated`
- Use the exact path parameter values shown in the examples

## Auth

## Users

## Books

## Shelf

## Authors

## Series

## Reviews

## Internal

## Admin, Schema, Docs
```

- [ ] **Step 2: Verify the skeleton matches the Django URL tree**

Run: `python - <<'PY'
from pathlib import Path
text = Path('backend-django/config/urls.py').read_text()
print('api/auth/' in text and 'api/users/' in text and 'api/books/' in text)
PY`
Expected: `True`

### Task 2: Write Auth examples

**Files:**
- Modify: `docs/backend/swagger_requests.md`
- Reference: `backend-django/users/views.py`
- Reference: `backend-django/users/urls/auth.py`

- [ ] **Step 1: Add Auth section content**

```markdown
## Auth

### `POST /api/auth/register/`

**Swagger UI input**

```json
{
  "email": "new.user@example.com",
  "username": "newuser",
  "password": "secret1234"
}
```

**Expected result**

- Status: `201 Created`
- Response: created user payload from `RegisterSerializer`

**Notes**

- Auth: not required
- Validation: serializer rejects invalid or missing fields

### `POST /api/auth/login/`

**Swagger UI input**

```json
{
  "email": "user@example.com",
  "password": "secret1234"
}
```

**Expected result**

- Status: `200 OK`
- Response: token payload from `LoginSerializer`

**Notes**

- Auth: not required

### `POST /api/auth/refresh/`

**Swagger UI input**

```json
{
  "refresh": "<refresh_token>"
}
```

**Expected result**

- Status: `200 OK`
- Response: new access token payload from SimpleJWT

**Notes**

- Auth: not required

### `POST /api/auth/logout/`

**Swagger UI input**

```json
{
  "refresh": "<refresh_token>"
}
```

**Expected result**

- Status: `200 OK`
- Response: `{ "message": "Logged out successfully" }`

**Notes**

- Auth: not required
- The refresh token is blacklisted when present

### `GET /api/auth/me/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: `{ "authenticated": true|false, "email": ..., "username": ..., "role": ... }`

**Notes**

- Auth: optional
```

- [ ] **Step 2: Verify status codes against `users/views.py`**

Run: `python - <<'PY'
from pathlib import Path
text = Path('backend-django/users/views.py').read_text()
print('201' in text and 'Logged out successfully' in text)
PY`
Expected: `True`

### Task 3: Write Users examples

**Files:**
- Modify: `docs/backend/swagger_requests.md`
- Reference: `backend-django/users/views.py`
- Reference: `backend-django/users/urls/users.py`

- [ ] **Step 1: Add Users section content**

```markdown
## Users

### `GET /api/users/me/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: current user settings payload from `UserSettingsSerializer`

**Notes**

- Auth: required

### `PATCH /api/users/me/`

**Swagger UI input**

```json
{
  "username": "newname",
  "profile_public": true
}
```

**Expected result**

- Status: `200 OK`
- Response: updated current user payload

**Notes**

- Auth: required

### `PATCH /api/users/me/visibility/?profilePublic=false`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: `{ "profile_public": false }`

**Notes**

- Auth: required

### `GET /api/users/{username}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: public profile payload

**Notes**

- Auth: not required
- If the profile is private and the requester is not the owner, expect `404 Not Found`

### `POST /api/users/{username}/follow/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `201 Created`
- Response: follow payload from `FollowSerializer`

**Notes**

- Auth: required
- Following yourself returns `400 Bad Request`
- Re-following returns `409 Conflict`

### `DELETE /api/users/{username}/follow/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- If the follow link does not exist, expect `404 Not Found`
```

- [ ] **Step 2: Verify user status codes and private-profile behavior**

Run: `python - <<'PY'
from pathlib import Path
text = Path('backend-django/users/views.py').read_text()
print('409' in text and 'Http404' in text and '204' in text)
PY`
Expected: `True`

### Task 4: Write Books examples

**Files:**
- Modify: `docs/backend/swagger_requests.md`
- Reference: `backend-django/books/views.py`
- Reference: `backend-django/books/urls.py`

- [ ] **Step 1: Add Books section content**

```markdown
## Books

### `GET /api/books/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of books

**Notes**

- Auth: not required
- Query: optional `q` filter

### `POST /api/books/`

**Swagger UI input**

```json
{
  "title": "Example Book",
  "description": "Example description",
  "author_id": 1,
  "tags": ["fantasy", "drama"]
}
```

**Expected result**

- Status: `201 Created`
- Response: created book payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `GET /api/books/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: detailed book payload with authors, tags, chapters, characters, and relations

**Notes**

- Auth: not required

### `PATCH /api/books/{id}/`

**Swagger UI input**

```json
{
  "title": "Updated Title"
}
```

**Expected result**

- Status: `200 OK`
- Response: updated book payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `DELETE /api/books/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `GET /api/books/{book_id}/chapters/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of chapters sorted by `chapter_number`

**Notes**

- Auth: not required

### `POST /api/books/{book_id}/chapters/`

**Swagger UI input**

Use `multipart/form-data` with a file field named `file` containing chapter text.

**Expected result**

- Status: `201 Created`
- Response: `{ "bookId": <id>, "chaptersCreated": <number> }`

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`
- Missing file returns `400 Bad Request`

### `DELETE /api/books/{book_id}/chapters/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `GET /api/books/{book_id}/characters/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of character records

**Notes**

- Auth: not required

### `GET /api/books/{book_id}/relations/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of character relation records

**Notes**

- Auth: not required
```

- [ ] **Step 2: Verify book status codes and multipart upload behavior**

Run: `python - <<'PY'
from pathlib import Path
text = Path('backend-django/books/views.py').read_text()
print('201' in text and 'multipart' not in text and 'No file provided' in text)
PY`
Expected: `True`

### Task 5: Write Shelf, Authors, Series, Reviews, Internal, Admin sections

**Files:**
- Modify: `docs/backend/swagger_requests.md`
- Reference: `backend-django/shelf/views.py`
- Reference: `backend-django/library/views.py`
- Reference: `backend-django/reviews/views.py`
- Reference: `backend-django/analysis/urls.py`

- [ ] **Step 1: Add the remaining sections**

```markdown
## Shelf

### `GET /api/shelf/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of the authenticated user’s shelf entries

**Notes**

- Auth: required

### `GET /api/shelf/{book_id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: shelf entry payload

**Notes**

- Auth: required
- Missing entry returns `404 Not Found`

### `POST /api/shelf/{book_id}/`

**Swagger UI input**

```json
{
  "status": "WANT_TO_READ"
}
```

**Expected result**

- Status: `201 Created`
- Response: shelf entry payload

**Notes**

- Auth: required

### `PATCH /api/shelf/{book_id}/`

**Swagger UI input**

```json
{
  "status": "READING"
}
```

**Expected result**

- Status: `200 OK`
- Response: updated shelf entry payload

**Notes**

- Auth: required
- Missing `status` returns `400 Bad Request`

### `DELETE /api/shelf/{book_id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required

## Authors

### `GET /api/authors/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of authors

**Notes**

- Auth: not required

### `POST /api/authors/`

**Swagger UI input**

```json
{
  "name": "Example Author"
}
```

**Expected result**

- Status: `201 Created`
- Response: created author payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `GET /api/authors/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: author payload

**Notes**

- Auth: not required

### `PATCH /api/authors/{id}/`

**Swagger UI input**

```json
{
  "name": "Updated Author"
}
```

**Expected result**

- Status: `200 OK`
- Response: updated author payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `DELETE /api/authors/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

## Series

### `GET /api/series/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of series

**Notes**

- Auth: not required

### `POST /api/series/`

**Swagger UI input**

```json
{
  "name": "Example Series"
}
```

**Expected result**

- Status: `201 Created`
- Response: created series payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `GET /api/series/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: series payload

**Notes**

- Auth: not required

### `PATCH /api/series/{id}/`

**Swagger UI input**

```json
{
  "name": "Updated Series"
}
```

**Expected result**

- Status: `200 OK`
- Response: updated series payload

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

### `DELETE /api/series/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

## Reviews

### `GET /api/reviews/{book_id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of reviews for the book

**Notes**

- Auth: not required

### `POST /api/reviews/{book_id}/`

**Swagger UI input**

```json
{
  "content": "Great book!",
  "rating": 5
}
```

**Expected result**

- Status: `201 Created`
- Response: created review payload

**Notes**

- Auth: required

### `DELETE /api/reviews/{id}/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `204 No Content`
- Response: empty body

**Notes**

- Auth: required
- Role: `MODERATOR` or `ADMIN`

## Internal

### `POST /api/internal/chapters/{chapter_id}/analyse-result/`

**Swagger UI input**

```json
{
  "status": "accepted"
}
```

**Expected result**

- Status: `200 OK` or `204 No Content`, depending on callback implementation
- Response: callback-specific payload or empty body

**Notes**

- Auth: internal only

### `POST /api/internal/chapters/{chapter_id}/ner-result/`

**Swagger UI input**

```json
{
  "status": "accepted"
}
```

**Expected result**

- Status: `200 OK` or `204 No Content`, depending on callback implementation
- Response: callback-specific payload or empty body

**Notes**

- Auth: internal only

### `POST /api/internal/books/{book_id}/find-pairs-result/`

**Swagger UI input**

```json
{
  "status": "accepted"
}
```

**Expected result**

- Status: `200 OK` or `204 No Content`, depending on callback implementation
- Response: callback-specific payload or empty body

**Notes**

- Auth: internal only

### `POST /api/internal/books/{book_id}/relations-result/`

**Swagger UI input**

```json
{
  "status": "accepted"
}
```

**Expected result**

- Status: `200 OK` or `204 No Content`, depending on callback implementation
- Response: callback-specific payload or empty body

**Notes**

- Auth: internal only

## Admin, Schema, Docs

### `GET /api/schema/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: OpenAPI schema document

### `GET /api/docs/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: Swagger UI HTML page

### `GET /admin/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK` after login, otherwise redirect or login page
- Response: HTML admin interface

**Notes**

- Auth: browser session login required
```

- [ ] **Step 2: Verify the remaining sections match the current views**

Run: `python - <<'PY'
from pathlib import Path
files = [
    'backend-django/shelf/views.py',
    'backend-django/library/views.py',
    'backend-django/reviews/views.py',
]
for file in files:
    text = Path(file).read_text()
    print(file, '204' in text or '201' in text)
PY`
Expected: each file prints `True` for the status check

### Task 6: Review and commit the document

**Files:**
- Modify: `docs/backend/swagger_requests.md`

- [ ] **Step 1: Run a final content check**

Run: `python - <<'PY'
from pathlib import Path
text = Path('docs/backend/swagger_requests.md').read_text()
required = ['## Auth', '## Users', '## Books', '## Shelf', '## Authors', '## Series', '## Reviews', '## Internal', '## Admin, Schema, Docs']
print(all(section in text for section in required))
PY`
Expected: `True`

- [ ] **Step 2: Commit**

```bash
git add docs/backend/swagger_requests.md
git commit -m "docs: add swagger request examples for django endpoints"
```
