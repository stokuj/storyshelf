# ADR-003: Encje NER per-book, brak modelu Chapter

**Status:** Zaakceptowane
**Data:** 2026-05-13
**Supersedes:** pierwotny schemat z modelem `Chapter` + globalnymi tabelami encji

## Kontekst

Pierwotny schemat NLP zakładał:

- Model `Chapter` z polem `ner_pending` (JSONField) — przechowywał tymczasowe wyniki NER
  per rozdział, zanim `merge_book_ner` upsertował je do globalnych tabel
- Globalne tabele `Character`, `Place`, `Organization` z `name UNIQUE`
- 5 tasków Celery: `chunk_chapter` → `merge_chapter` → `merge_book` → `relations_for_book` → cleanup

Ten design powodował trzy problemy:

1. **Kolizje nazw** — "Jan" z książki A i "Jan" z książki B to dwie różne postacie, ale globalny
   unique constraint je zlewał w jeden rekord
2. **Race condition** — 5 tasków z zależnościami; przy równoległym uruchomieniu dwóch książek
   na tym samym worker pool wyniki nakładały się przy `merge_book`
3. **Chapter jako wyciek abstrakcji** — model `Chapter` istniał wyłącznie jako artefakt
   chunkingu NLP, nigdy nie był używany w UI ani logice domeny. Frontend pokazywał książki
   bez rozdziałów. Schemat zawierał coś, co nie miało odpowiednika w domenie.

## Opcje rozważone

1. **Status quo (Chapter + global entities)** — wszystkie powyższe problemy
2. **Chapter + per-book entities** — Chapter dalej zbędny, complexity 5 tasków pozostaje
3. **Bez Chapter, per-book entities** (wybrane) — chunking jako szczegół implementacji workera
4. **Bez Chapter, global entities + book M2M** — wymaga disambiguation logic ("który Jan?"),
   przesuwa problem zamiast go rozwiązać

## Decyzja

- Usunięcie modelu `Chapter`. Tekst książki w `Book.text` (TextField), czyszczony do `""`
  po zakończeniu pipeline'u
- `BookCharacter`, `BookPlace`, `BookOrganization` — każdy model ma:
  - FK `book` → `books.Book` z `related_name="characters" / "places" / "organizations"`
  - `unique_together("name", "book")` zamiast globalnego unique
- `CharacterRelationship`:
  - FK `from_character` → `BookCharacter`, `to_character` → `BookCharacter`
  - FK `book` → `books.Book`
  - `unique_together("from_character", "to_character", "book")`
  - 24 typy relacji jako choices na `relation_type`
- Chunking 400 słów z overlap 50 wewnątrz `analyse_book.delay(book_id)` — funkcja `chunk_text()`
  w `analysis/ner_engine.py`
- Pipeline redukuje się z 5 do 2 tasków: `analyse_book` (NER, queue `ner`) + `relations_for_book`
  (LLM, queue `llm`)

## Konsekwencje

- **`analyse_book` nie jest idempotentny** — ponowne uruchomienie z nowym tekstem akumuluje
  encje. Twarda reguła w wiki: ręczne `BookCharacter.objects.filter(book=...).delete()` (i analogicznie
  dla Place/Organization) przed re-analizą. Jest to znane ograniczenie — patrz pozycja w ROADMAP
  ("Idempotentność analyse_book")
- **Brak cross-book queries po nazwie** — nie da się zapytać "wszystkie książki, w których pojawia
  się Frodo" bez agregowania po nazwie przez wszystkie `BookCharacter`. Niewielka strata —
  cross-book character search nie jest wymaganiem MVP
- **Disambiguation aliasów** ("Frodo" vs "Frodo Baggins") nadal istnieje **w obrębie jednej książki** —
  to osobny problem, na ROADMAP jako kolejny etap
- **BookDetail API response**: `{book, shelfEntry, characters, relations}` — bez klucza `chapters`
- **Migracje**: w dev używamy `manage.py flush --no-input && manage.py migrate` zamiast pisania
  migration plików — patrz CLAUDE.md ("Twarde reguły")
- **`NER_MIN_OCCURRENCES`** (env var, default 5) filtruje encje o niskiej częstotliwości — przy
  testowaniu z małymi tekstami ustaw na 1

## Linki

- Kod: `backend-django/analysis/models.py`, `backend-django/analysis/tasks.py`, `backend-django/analysis/ner_engine.py`
- Strony wiki: [[nlp-pipeline]]
- Supersedes: wcześniejszy design opisany w usuniętym `docs/superpowers/plans/2026-05-13-nlp-pipeline-redesign.md`
