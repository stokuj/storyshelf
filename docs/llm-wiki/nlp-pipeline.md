---
title: NLP Pipeline
last_updated: 2026-05-22
last_verified_commit: 86ea9b0
owns:
  - backend-django/analysis/tasks.py
  - backend-django/analysis/ner_engine.py
  - backend-django/analysis/llm_engine.py
  - backend-django/analysis/models.py
  - backend-django/analysis/text_parser.py
depends_on:
  - spaCy en_core_web_trf (CPU-only torch)
  - OpenRouter API
  - RabbitMQ (queues: ner, llm)
related_pages: [celery-workers, dev-setup]
status: stable
---

## Co to jest

Pipeline analizy literackiej książek: ekstrakcja postaci/miejsc/organizacji (NER przez spaCy)
i relacji między postaciami (LLM przez OpenRouter). Wynik per-książka w tabelach
`BookCharacter`, `BookPlace`, `BookOrganization`, `CharacterRelationship`.

## Jak działa

```
Admin uploaduje tekst do Book.text przez Django Admin
    ↓
Admin wybiera książki → akcja "Analyse selected books" → analyse_book.delay(book_id) per książka
    ↓
[Queue: ner, worker: celery-ner, pool: prefork]

analyse_book(book_id):
    1. Pobierz Book.text
    2. chunk_text(text, chunk_size=400, overlap=50)  # word-based chunking
    3. nlp.pipe(chunks) — spaCy en_core_web_trf na CPU
    4. Counter encji po typach (PERSON, LOC, ORG)
    5. Filtr: tylko encje z count >= NER_MIN_OCCURRENCES (default 5)
    6. Upsert BookCharacter / BookPlace / BookOrganization z book FK
    7. find_sentences_with_both_characters()  # regex, synchronicznie, znajduje pary
    8. Book.text = ""  # czyszczenie
    9. relations_for_book.delay(book_id, pairs_data)
    ↓
[Queue: llm, worker: celery-llm, pool: gevent]

relations_for_book(book_id, pairs_data):
    for pair in pairs_data:
        try:
            prompt = build_prompt(pair, sentences)
            response = OpenRouter.chat(LLM_MODEL, prompt)
            CharacterRelationship.objects.get_or_create(
                book=book, from_character=A, to_character=B,
                defaults={"relation_type": parsed_type}
            )
        except Exception:
            log.warning(...)  # skip, no retry per pair
```

## Decyzje

- Brak modelu `Chapter`, encje per-book: patrz [ADR-003](../decisions/ADR-003-encje-ner-per-book.md)
- Dwa osobne workery (prefork dla NER, gevent dla LLM): patrz [ADR-002](../decisions/ADR-002-dwa-workery-celery.md)
- spaCy `en_core_web_trf` CPU-only zamiast natywnego BERT: ~400 MB vs ~2.5 GB obrazu Docker,
  wystarczająca jakość NER dla literatury angielskiej, brak konieczności GPU na VPS

## Typowe operacje

**Manualne uruchomienie analizy:**
```python
# Z Django shell
from analysis.tasks import analyse_book
analyse_book.delay(book_id=42)
```

**Re-analiza książki (która już była analizowana):**
```python
# 1. Wyczyść stare encje (analyse_book NIE jest idempotentny)
from analysis.models import BookCharacter, BookPlace, BookOrganization, CharacterRelationship
book_id = 42
BookCharacter.objects.filter(book_id=book_id).delete()
BookPlace.objects.filter(book_id=book_id).delete()
BookOrganization.objects.filter(book_id=book_id).delete()
CharacterRelationship.objects.filter(book_id=book_id).delete()

# 2. Wgraj tekst ponownie do Book.text (przez admin lub ORM)
# 3. analyse_book.delay(book_id)
```

**Testowanie z małym tekstem:**
```bash
# Ustaw próg detekcji na 1 — inaczej małe teksty nie wygenerują żadnych encji
NER_MIN_OCCURRENCES=1 DJANGO_ENV=dev uv run python -m pytest analysis/tests/
```

**Sprawdzenie wyników w admin:**
- `http://localhost:8000/admin/analysis/bookcharacter/?book__id__exact=42`

## Pułapki

- **`analyse_book` NIE jest idempotentny** — re-uplaod tekstu i ponowne uruchomienie akumuluje
  encje. Patrz "Typowe operacje" — manualne czyszczenie wymagane.
- **`NER_MIN_OCCURRENCES` default 5** — przy testach z małymi tekstami otrzymasz 0 encji bez
  zmiany tej zmiennej.
- **Encje są per-book**, unique_together(name, book). "Frodo" w książce A i B to dwa różne rekordy.
- **Brak modelu Chapter** — był usunięty, tekst całej książki w `Book.text`. Frontend BookDetail
  zwraca `{book, shelfEntry, characters, relations}` bez `chapters`.
- **`Book.text` czyszczony po analizie** — `analyse_book` ustawia `Book.text = ""` na końcu.
  Jeśli potrzebujesz tekstu do debugowania, zachowaj kopię przed uruchomieniem.
- **LLM module-level init**: `LLMService()` instantiates at import time w `llm_engine.py`.
  `analysis/tasks.py` wraps the import in try/except, żeby testy nie wymagały `OPENROUTER_API_KEY`.
- **`Serie` model** (library/models.py) jest singularny — "Series" koliduje z mechanizmem
  test discovery Django.
- **CharacterRelationSerializer** wystawia `relation_type` (nie `relation`!). Brak pola `evidence`
  — nie próbuj go używać po stronie frontu.
- **spaCy Python pin**: `pyproject.toml` ma `requires-python = ">=3.13,<3.14"` bo
  `en_core_web_trf` nie ma jeszcze wheela cp314.

## Pytania, na które ta strona odpowiada

- Jak działa analiza tekstu książki w StoryShelf?
- Czemu są 2 osobne workery Celery?
- Jak ponownie przeanalizować książkę, którą już raz przepuściłem?
- Czemu moja analiza nie zwraca żadnych encji?
- Czym różni się `BookCharacter` od `Character`?
- Czemu nie ma modelu Chapter?
- Co się dzieje z `Book.text` po analizie?
- Jak debugować błędy LLM w `relations_for_book`?
- Czemu testy NLP wymagają `DJANGO_ENV=dev`?
