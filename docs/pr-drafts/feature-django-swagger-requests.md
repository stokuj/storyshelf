## Why

We need a single, copy-paste-friendly reference for manually testing Django endpoints in Swagger UI. The goal is to make it easy to validate request bodies, path parameters, and expected HTTP responses without reading view code first.

## What

- Added `docs/backend/swagger_requests.md` with Swagger UI request examples grouped by Django app.
- Documented auth, users, books, shelf, authors, series, reviews, internal callbacks, and admin/schema/docs routes.
- Included expected status codes and response shapes for each endpoint.
- Added planning and design docs for the new request guide.

## Testing

- [ ] Manual review: confirm each endpoint example matches the current Django `urls.py` and view behavior.
- [ ] Manual review: check the expected status codes for auth, CRUD, and internal callback endpoints.

## Rollback

`git revert a345b12 7e5a6ca` — removes the request guide and the related planning docs.

## Risk

Low — documentation-only change, no runtime behavior or API contracts were modified.
