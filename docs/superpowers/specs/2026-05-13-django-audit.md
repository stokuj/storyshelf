# Django Backend Audit — Spec

**Data:** 2026-05-13  
**Zakres:** backend-django/  
**Stan wyjściowy:** 90 testów ✅, ruff 80+ naruszeń, Django 6.0.5 / DRF 3.17.1 / Celery 5.6.3

---

## Kontekst

Backend jest funkcjonalny i testy przechodzą, ale ma dług techniczny w czterech obszarach:
integralność danych w modelach, jakość kodu (lint), walidacja wejść oraz pokrycie testami.
Celem audytu jest doprowadzenie kodu do stanu gotowego do wdrożenia produkcyjnego.

---

## Obszar 1 — Relacje i modele

### Znalezione problemy

| Problem | Plik | Ryzyko |
|---|---|---|
| `Book.isbn` — brak `unique=True` | `books/models.py:30` | Duplikaty książek w bazie |
| `Author.name` — brak `unique=True` | `library/models.py:4` | Duplikaty autorów |
| `Book.title` — `blank=True, default=""` | `books/models.py:28` | Książki bez tytułu w bazie |
| `Book.year` — `default=0`, brak walidacji | `books/models.py:29` | Rok 0 lub ujemny możliwy |
| `Book.page_count` — `default=0`, brak walidacji | `books/models.py:32` | Liczba stron 0 lub ujemna |
| `ShelfEntry.finish_date` — brak walidacji vs `start_date` | `shelf/models.py` | `finish_date < start_date` możliwe |
| Brak indeksów DB na FK często filtrowanych | `reviews/models.py`, `shelf/models.py` | Powolne zapytania przy wzroście danych |

### Planowane zmiany

1. Dodaj `unique=True` do `Book.isbn` (nullable — pozwól na `null` zamiast `""` dla książek bez ISBN)
2. Dodaj `unique=True` do `Author.name`
3. Usuń `blank=True` z `Book.title` — tytuł jest wymagany
4. Dodaj `MinValueValidator(1)` do `Book.year` i `Book.page_count`
5. Dodaj `clean()` na `ShelfEntry` walidujący `finish_date >= start_date`
6. Dodaj `db_index=True` na `Review.book`, `Review.user`, `ShelfEntry.user`, `ShelfEntry.book`
7. Nowe migracje dla wszystkich zmian

---

## Obszar 2 — Lint i konwencje

### Znalezione problemy

| Kod | Liczba | Opis | Akcja |
|---|---|---|---|
| `I001` | 37 | Niesortowane importy | Auto-fix `ruff --fix` |
| `E501` | ~30 | Linie > 100 znaków | Migracjom — `# noqa`, reszta ręcznie |
| `N815` | 15 | camelCase w class scope | `# noqa: N815` — celowe (frontend API) |
| `E501` | 1 | `SPECTACULAR_SETTINGS` w `base.py:124` | Przenieś na wiele linii |

### Planowane zmiany

1. `uv run ruff check --fix .` — auto-naprawa 37 importów
2. Migracjom dodaj `# noqa: E501` per linia lub `per-file-ignores` w `pyproject.toml`
3. Serializatorom z camelCase dodaj `# noqa: N815` lub dodaj `per-file-ignores` dla plików serializatorów
4. Podziel `SPECTACULAR_SETTINGS` w `base.py` na wiele linii
5. Weryfikacja: `uv run ruff check .` → 0 błędów

---

## Obszar 3 — Walidacja danych

### Znalezione problemy

| Problem | Plik | Opis |
|---|---|---|
| `Book.title` może być `""` | `books/serializers.py` | Brak `min_length` w serializatorze |
| `Book.year` bez zakresu w serializatorze | `books/serializers.py` | Walidacja tylko w modelu |
| `isbn` format niezwalidowany | `books/serializers.py` | Akceptuje dowolny string |
| `RegisterSerializer.username` — tylko małe litery `^[a-z]{3,30}$` | `users/serializers.py:12` | Brak cyfr/underscore — sprawdzić czy celowe |
| `ShelfEntry.status` — brak walidacji wartości w serializatorze | `shelf/serializers.py` | DRF przyjmuje tylko choices — ok, ale brak custom error msg |
| Brak walidacji `bookId` istnienia w `ReviewCreateSerializer` | `reviews/serializers.py` | FK constraint łapie błąd, ale 500 zamiast 400 |

### Planowane zmiany

1. Dodaj `min_length=1` na `title` w serializatorze książki (jeśli endpoint tworzenia istnieje)
2. Dodaj walidację `book_id` w `ReviewCreateSerializer.validate()` — zwróć 400 jeśli książka nie istnieje
3. Zachowaj regex na username — jest celowy (prosty slug)
4. Dodaj `MinValueValidator` na polach modelu (opisane w Obszarze 1)

---

## Obszar 4 — Testy i pokrycie

### Znalezione problemy

| Brak testu | Opis |
|---|---|
| Sygnał `avg_rating` | Brak testu że `Book.avg_rating` aktualizuje się po dodaniu/usunięciu Review |
| `ShelfEntry.clean()` | Po dodaniu walidacji dat — potrzebne testy |
| `Genre` endpoints | Brak jakichkolwiek testów dla `GenreListView` / `GenreRetrieveView` |
| `UserVisibilityView` | Brak testu PATCH `?profilePublic=false` |
| `BookCreateView` | Nie istnieje endpoint — tylko Admin; ok |
| Pokrycie kodu | Brak `pytest-cov` — nie wiadomo jaki % kodu jest pokryty |

### Planowane zmiany

1. Dodaj `pytest-cov` do `[dependency-groups] dev` w `pyproject.toml`
2. Dodaj konfigurację coverage w `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   DJANGO_SETTINGS_MODULE = "config.settings"
   
   [tool.coverage.run]
   source = ["."]
   omit = ["*/migrations/*", "*/.venv/*", "*/tests/*", "manage.py"]
   ```
3. Dodaj testy sygnału `avg_rating` w `reviews/tests/test_signals.py`
4. Dodaj testy `Genre` endpoints w `library/tests/test_views.py`
5. Dodaj test `UserVisibilityView` w `users/tests/test_users.py`
6. Dodaj testy `ShelfEntry.clean()` po implementacji walidacji dat
7. Cel pokrycia: sprawdzić baseline, dążyć do >80% na kluczowych appkach

---

## Poza zakresem

- Pakiety: Django 6.0.5, DRF 3.17.1, Celery 5.6.3 — **aktualne, bez akcji**
- JWT dev key warning — dev-only, nie produkcja
- `BookCharacter` global (bez FK do Book) — celowa decyzja architektoniczna
- Admin-only tworzenie książek/autorów — bez zmian

---

## Weryfikacja końcowa

```bash
# Lint — 0 błędów
uv run ruff check .

# Testy — wszystkie zielone
DJANGO_ENV=dev uv run python manage.py test

# Migracje — żadnych pending
DJANGO_ENV=dev uv run python manage.py migrate --check

# System check
uv run python manage.py check

# Pokrycie
DJANGO_ENV=dev uv run python -m pytest --cov --cov-report=term-missing
```
