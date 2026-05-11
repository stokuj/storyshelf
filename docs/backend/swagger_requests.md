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

## Users

### `GET /api/users/me/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: current user settings payload with `username`, `email`, `bio`, `avatarUrl`, `role`, `profilePublic`, and `memberSince`

**Notes**

- Auth: required

### `PATCH /api/users/me/`

**Swagger UI input**

```json
{
  "username": "newname",
  "bio": "Updated bio",
  "avatarUrl": "https://example.com/avatar.jpg",
  "profilePublic": true
}
```

**Expected result**

- Status: `200 OK`
- Response: updated current user payload with the same field set as `UserSettingsSerializer`

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
- Response: public profile payload with `username`, `bio`, `avatarUrl`, and `memberSince`

**Notes**

- Auth: not required
- If the profile is private and the requester is not the owner, expect `404 Not Found`

### `POST /api/users/{username}/follow/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `201 Created`
- Response: follow payload with `id`, `followerUsername`, `followingUsername`, and `followedAt`

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
  "author_id": 1,
  "year": 2024,
  "isbn": "9781234567897",
  "description": "Example description",
  "page_count": 320,
  "genres": ["fantasy"],
  "tags": ["drama"]
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
- Response: wrapper payload with `book`, `shelfEntry`, `chapters`, `reviews`, `characters`, and `relations`

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

### `GET /api/books/{book_id}/reviews/`

**Swagger UI input**

No request body.

**Expected result**

- Status: `200 OK`
- Response: flat list of reviews for the book

**Notes**

- Auth: not required

### `POST /api/books/{book_id}/reviews/`

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
  "char_count": 1200,
  "char_count_clean": 1000,
  "word_count": 220,
  "token_count": 260
}
```

**Expected result**

- Status: `200 OK`
- Response: empty body

**Notes**

- Auth: internal only

### `POST /api/internal/chapters/{chapter_id}/ner-result/`

**Swagger UI input**

```json
{
  "result": {
    "characters": {
      "Alice": 3,
      "Bob": 2
    }
  }
}
```

**Expected result**

- Status: `200 OK`
- Response: empty body

**Notes**

- Auth: internal only

### `POST /api/internal/books/{book_id}/find-pairs-result/`

**Swagger UI input**

```json
{
  "pairs": [
    {
      "pair": ["Alice", "Bob"]
    }
  ]
}
```

**Expected result**

- Status: `200 OK`
- Response: empty body

**Notes**

- Auth: internal only

### `POST /api/internal/books/{book_id}/relations-result/`

**Swagger UI input**

```json
{
  "all_relations": [
    {
      "relations": {
        "relations": [
          {
            "source": "Alice",
            "target": "Bob",
            "relation": "friends",
            "evidence": "They travel together.",
            "confidence": 0.92
          }
        ]
      }
    }
  ]
}
```

**Expected result**

- Status: `200 OK`
- Response: empty body

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

## Entry Format

Use this pattern for each endpoint:

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
