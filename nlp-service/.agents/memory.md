# Memory

## Project
NLP: użytkownik podaje treść książki, a system z użyciem spaCy zwraca listę postaci.

## Core flow
1. Wejście: tekst książki.
2. spaCy: tokenizacja i NER (`PERSON`).
3. Post-processing: deduplikacja i normalizacja aliasów.
4. Wyjście: unikalna lista postaci (opcjonalnie z licznością).

## Notes
- Model spaCy dobierać do języka tekstu.
- Traktować NER jako heurystykę: możliwe pominięcia i fałszywe trafienia.
- Przed pracą czytać `AGENTS.md` i `.agents/memory.md`.
- Dla zadań powtarzalnych używać skilli z `.agents/skills/`.
- Punkt wejścia aplikacji przeniesiony do `src/main.py`.
- Bazowy przykład aplikacji: "Hello NLP" + ekstrakcja postaci (`PERSON` / `persName`) ze spaCy.
- W przykładach domyślnie używamy języka angielskiego (tekst i komunikaty).
- Domyślny model spaCy dla przykładu: `en_core_web_sm`.
- CLI obsługuje wejście plikowe przez `--input`.
- Wspierane formaty wejścia: `.txt`, `.md`, `.epub`, `.pdf`.
- Domyślny model podniesiony do `en_core_web_trf` z fallbackiem do `en_core_web_sm`.
