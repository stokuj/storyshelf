# Agents

## Cel projektu
NLP: użytkownik podaje treść książki, a system z użyciem spaCy zwraca listę postaci.

## Pipeline
1. Wejście: tekst książki (plik lub string).
2. Przetwarzanie spaCy:
   - tokenizacja,
   - NER (encje typu `PERSON`).
3. Post-processing:
   - deduplikacja nazw,
   - podstawowa normalizacja aliasów i wariantów zapisu.
4. Wyjście: unikalna lista postaci (opcjonalnie z liczbą wystąpień).

## Założenia
- Model spaCy dobieramy do języka książki.
- Priorytet: czytelna i możliwie precyzyjna lista postaci.
- Ograniczenie: NER może pomijać rzadkie imiona i mylić niektóre nazwy własne.

## Memory
- Plik pamięci projektu: `.agents/memory.md`.
- Zawiera trwałe ustalenia, decyzje i ważny kontekst domenowy.
- Rozkaz: przed rozpoczęciem pracy przeczytaj `.agents/memory.md`, a po zmianach zaktualizuj go, jeśli pojawiły się nowe trwałe decyzje.

## Skills
- Katalog umiejętności: `.agents/skills/`.
- Każdy skill opisuje powtarzalny workflow (np. ekstrakcja postaci, normalizacja aliasów, walidacja wyników).
- Rozkaz: gdy zadanie pasuje do istniejącego skilla, użyj go jako domyślnej procedury i trzymaj się jego kroków.
- Jeśli brakuje skilla dla powtarzalnego procesu, dodaj nowy plik skill w `.agents/skills/`.
