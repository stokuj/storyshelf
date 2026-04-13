# SpringShelf API Endpoints

This document describes currently exposed Spring endpoints grouped by business area.

## Authentication

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register account |
| POST | `/api/auth/login` | Public | Login (session-based) |
| GET | `/api/auth/me` | Public/Auth-aware | Return current session identity |
| POST | `/api/auth/logout` | Authenticated | Logout and invalidate session |

## Books

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/books` | Public | Search/browse books |
| GET | `/api/books/{id}` | Public | Basic book details |
| GET | `/api/books/{id}/details` | Public | Aggregated details (chapters, characters, relations, reviews, shelf state) |
| POST | `/api/books` | MODERATOR | Create book |
| PUT | `/api/books/{id}` | MODERATOR | Full update |
| PATCH | `/api/books/{id}` | MODERATOR | Partial update |
| DELETE | `/api/books/{id}` | MODERATOR | Delete book |

## Chapters and Analysis Trigger

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/books/{bookId}/chapters` | Public | List chapters for book |
| POST | `/api/books/{bookId}/chapters` | MODERATOR | Upload `.txt`, split into chapters, trigger async NLP pipeline |
| DELETE | `/api/books/{bookId}/chapters` | MODERATOR | Remove chapter content for book |

## Characters and Relations

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/books/{bookId}/characters` | Public | List extracted characters for book |
| GET | `/api/books/{bookId}/relations` | Public | List extracted character relations for book |

## Authors

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/authors` | Public | List authors |
| GET | `/api/authors/{id}` | Public | Author details |
| POST | `/api/authors` | MODERATOR | Create author |
| PUT | `/api/authors/{id}` | MODERATOR | Update author |
| DELETE | `/api/authors/{id}` | MODERATOR | Delete author |

## Series

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/series` | Public | List series |
| GET | `/api/series/{id}` | Public | Series details |
| POST | `/api/series` | MODERATOR | Create series |
| PUT | `/api/series/{id}` | MODERATOR | Update series |
| DELETE | `/api/series/{id}` | MODERATOR | Delete series |

## Reviews

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/books/{id}/reviews` | Public | List reviews for book |
| POST | `/api/books/{id}/reviews` | USER | Add review |
| DELETE | `/api/reviews/{id}` | MODERATOR | Delete review |

## User Profile and Follow

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/users/{username}` | Public | Public profile |
| GET | `/api/users/me` | USER | Own profile/settings |
| PUT | `/api/users/me` | USER | Update own profile |
| PATCH | `/api/users/me/visibility` | USER | Set public/private profile |
| POST | `/api/users/{username}/follow` | USER | Follow user |
| DELETE | `/api/users/{username}/follow` | USER | Unfollow user |
| GET | `/api/users/{username}/followers` | USER | Followers list |
| GET | `/api/users/{username}/following` | USER | Following list |

## Bookshelf

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/shelf` | USER | Get my shelf |
| POST | `/api/shelf/{bookId}` | USER | Add book to shelf |
| GET | `/api/shelf/{bookId}` | USER | Get shelf entry for book |
| PATCH | `/api/shelf/{bookId}` | USER | Update shelf status |
| DELETE | `/api/shelf/{bookId}` | USER | Remove from shelf |
