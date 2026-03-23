# User Stories

This document describes the functional requirements and goals for different user roles in the SpringShelf application.

## Roles Definition
- **GUEST**: Unauthenticated visitor.
- **USER**: Authenticated library member.
- **MODERATOR**: Content manager with administrative access.
- **ADMIN**: System administrator with full control.

---

## 🟢 Current State (Implemented)

### GUEST
- As a `GUEST`, I can **register** a new account.
- As a `GUEST`, I can **log in** using my email and password.
- As a `GUEST`, I can **browse and search** the book catalog by title, author, or genre.
- As a `GUEST`, I can **view book details**, including characters, relations, and statistics.
- As a `GUEST`, I can **view public user profiles**.

### USER (Authenticated)
- As a `USER`, I can **manage my bookshelf** (add/remove books, update reading status).
- As a `USER`, I can **rate and review** books.
- As a `USER`, I can **follow/unfollow** other users to see their reading activity.
- As a `USER`, I can **edit my profile** (username, bio, avatar) and set it to public or private.
- As a `USER`, I receive **clear error messages** if I provide invalid data (e.g., rating out of scale).

### MODERATOR
- As a `MODERATOR`, I can **perform full CRUD** (Create, Read, Update, Delete) on the book catalog.
- As a `MODERATOR`, I can **manage authors and series** (add new entries, edit existing ones).
- As a `MODERATOR`, I can **upload book content** (.txt files) to trigger NLP analysis.
- As a `MODERATOR`, I can **manage chapter data** and clear analysis results.

---

## 🟡 TODO (Planned Features)

### USER
- As a `USER`, I can **submit book proposals** if a book is missing from the catalog.
- As a `USER`, I can **log in via GitHub** (OAuth2 integration stabilization).

### MODERATOR
- As a `MODERATOR`, I can **approve or reject** user book proposals.
- As a `MODERATOR`, I can **hide inappropriate reviews**.

### ADMIN
- As an `ADMIN`, I can **manage user roles** and ban accounts.
- As an `ADMIN`, I can **monitor system health** (Kafka, Worker status).
