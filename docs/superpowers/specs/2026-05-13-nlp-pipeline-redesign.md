# NLP Pipeline Redesign — Spec

**Data:** 2026-05-13  
**Zakres:** backend-django/analysis/, backend-django/books/

---

## Kontekst

Aktualny pipeline NLP ma kilka problemów: PyTorch z CUDA (~2.5 GB obraz), `Chapter` model który miesza domenę z implementacją NLP, `find_pairs` wywołuje LLM synchronicznie zamiast `.delay()`, `full_text` leci przez RabbitMQ, race condition w `ner_chapter`, `BookCharacter` globalny bez FK do Book.

Projekt jest personalny, skala 5-30 książek, trigger manualny przez Admin. Docelowo NER i LLM będą wywoływane niezależnie.

---

## Nowy pipeline

```
Admin uploaduje TXT → Book.text
Admin triggeruje → analyse_book.delay(book_id)

analyse_book (kolejka: ner, CPU-bound):
    1. Czyta Book.text
    2. Chunkuje fixed-size z overlapem (spaCy nlp.pipe())
    3. NER → agreguje BookCharacter/BookPlace/BookOrganization (per book)
    4. find_sentences_with_both_characters() synchronicznie na pełnym tekście
    5. Book.text = "" (czyści)
    6. relations_for_book.delay(book_id, pairs_data)

relations_for_book (kolejka: llm, I/O-bound):
    1. LLM per para postaci → CharacterRelationship
    2. Błędy API pomijane (log + continue), brak retry
```

---

## Zmiany modeli

### Usuń: `Chapter` model (`books/models.py`)
- Usuń klasę `Chapter`
- Usuń `chapters_count` i `ner_completed_count` z `Book`
- Dodaj `Book.text = models.TextField(blank=True, default="")`

### Zmień: `BookCharacter`, `BookPlace`, `BookOrganization` (`analysis/models.py`)
- Dodaj `book = models.ForeignKey("books.Book", on_delete=models.CASCADE, related_name=..., null=True)`  
  (null=True tylko na czas migracji — po resecie DB zmień na null=False)
- Usuń `unique=True` z `name`
- Dodaj `unique_together = ("name", "book")`

### Usuń: `CharacterRelationship` — bez zmian (ma już `book` FK)

---

## Zmiany tasks.py

### Usuń taski:
- `analyse_chapter`
- `ner_chapter`
- `merge_book_ner`
- `find_pairs`

### Nowy task: `analyse_book(book_id)`
```python
@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def analyse_book(self, book_id: int):
    # 1. Pobierz Book.text
    # 2. Chunkuj z overlapem używając spaCy
    # 3. NER → upsert BookCharacter/BookPlace/BookOrganization z book FK
    # 4. find_sentences_with_both_characters() na pełnym tekście
    # 5. Book.text = ""
    # 6. relations_for_book.delay(book_id, pairs_data)
```

### Zmień task: `relations_for_book(book_id, pairs_data)`
- Dodaj `.delay()` (było wywołanie synchroniczne z find_pairs)
- Błędy API: `logger.warning(...)` + `continue`, bez `self.retry()`

---

## Zmiany NER engine (`analysis/ner_engine.py`)

Zastąp `transformers.pipeline` przez **spaCy**:

```python
import spacy

def load_ner_model(model: str = "en_core_web_trf") -> bool: ...
def extract_entities(text: str, model: str = "en_core_web_trf") -> dict: ...
```

Chunkowanie: `nlp.pipe(chunks)` gdzie chunk = ~400 tokenów z overlapem 50.
Deduplikacja encji między chunkami przez `Counter` (jak teraz).

---

## Zmiany `pyproject.toml`

```toml
# Usuń:
"torch>=2.10",
"transformers>=4.57",

# Dodaj:
"spacy>=3.7",
"en-core-web-trf @ https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl",

# PyTorch CPU-only (wymagany przez en_core_web_trf):
[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cpu" }
```

---

## Zmiany serializers/views

### `books/serializers.py`
- Usuń `BookCharacterSerializer` import `Chapter`
- Usuń `chapters` z `BookDetailSerializer`
- `CharacterRelationSerializer` — bez zmian

### `books/views.py`
- Usuń `Prefetch("chapters", ...)` z `BookRetrieveView.get_queryset()`

---

## Zmiany admin.py

### `analysis/admin.py`
- Usuń `analyze_selected_books` action (stary, per-rozdział)
- Dodaj nową akcję `analyse_selected_books` → `analyse_book.delay(book.id)` per książka

### `books/admin.py`
- Dodaj inline upload pola `text` na `BookAdmin`

---

## Reset DB

Po zmianach modeli: `manage.py flush --no-input && manage.py migrate`

Seed: `uv run python ../infra/scripts/seed.py`

---

## Weryfikacja

```bash
# Testy
DJANGO_ENV=dev uv run python manage.py test analysis books -v 2

# Lint
uv run ruff check .

# System check
uv run python manage.py check

# Ręczny test pipeline (w Django shell):
# 1. Utwórz Book z krótkim tekstem
# 2. Wywołaj analyse_book.delay(book.id)
# 3. Sprawdź BookCharacter.objects.filter(book=book)
# 4. Sprawdź CharacterRelationship.objects.filter(book=book)
```
