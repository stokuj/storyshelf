# Manual tests of using java endpoint based of User stories.

## GUEST

### Register
As a `GUEST`, I can **register** a new account.
Register						
Expected	Actual	Status	USERNAME	EMAIL	HASŁO1	HASŁO2

| ID | USERNAME | EMAIL | HASŁO1 | HASŁO2 | Expected | Actual | Status |
|----|----------|-------|--------|--------|----------|--------|--------|
| TC01 | user123 | user@test.com | Haslo123! | Haslo123! | Rejestracja udana |  |  |
| TC02 | u | user@test.com | Haslo123! | Haslo123! | Błąd: za krótki login |  |  |
| TC03 | user@123 | user@test.com | Haslo123! | Haslo123! | Błąd: niepoprawny login |  |  |
| TC04 | user123 | usertest.com | Haslo123! | Haslo123! | Błąd: niepoprawny email |  |  |
| TC05 | user123 | user@test.com | 123 | 123 | Błąd: za słabe hasło |  |  |
| TC06 | user123 | user@test.com | Haslo123! | Haslo123 | Błąd: hasła się różnią |  |  |
| TC07 |  | user@test.com | Haslo123! | Haslo123! | Błąd: pusty login |  |  |
| TC08 | user123 |  | Haslo123! | Haslo123! | Błąd: pusty email |  |  |
| TC09 | user123 | user@test.com |  |  | Błąd: puste hasło |  |  |

### Login
As a `GUEST`, I can **log in** using my email and password.

### Search Book
As a `GUEST`, I can **browse and search** the book catalog by title, author, or genre.

### View Book details
As a `GUEST`, I can **view book details**, including characters, relations, and statistics.

### View public User profile
As a `GUEST`, I can **view public user profiles**.

## USER (Authenticated)
- As a `USER`, I can **manage my bookshelf** (add/remove books, update reading status).
- As a `USER`, I can **rate and review** books.
- As a `USER`, I can **follow/unfollow** other users to see their reading activity.
- As a `USER`, I can **edit my profile** (username, bio, avatar) and set it to public or private.
- As a `USER`, I receive **clear error messages** if I provide invalid data (e.g., rating out of scale).

## MODERATOR
- As a `MODERATOR`, I can **perform full CRUD** (Create, Read, Update, Delete) on the book catalog.
- As a `MODERATOR`, I can **manage authors and series** (add new entries, edit existing ones).
- As a `MODERATOR`, I can **upload chapter content** (`.txt`) for a book.
- As a `MODERATOR`, after upload, I can rely on **automatic NLP pipeline execution** (analyse -> NER -> find-pairs -> relations) handled asynchronously via Kafka and worker services.
- As a `MODERATOR`, I can **clear chapter content and reset analysis-derived data** for a book when reprocessing is needed.