---
description: Po code review — zaproponuj zmiany w docs/llm-wiki/ na podstawie diffu gałęzi.
---

# /wiki-ingest

**Status: SZKIELET.** Pełna implementacja po pierwszych 3-5 PR-ach z ręczną aktualizacją wiki.
Dokument SDD ostrzega: **auto-aktualizacja po każdym mergu = śmieci.** Ingest jest
**pre-merge requirement**, nie post-merge hook.

## Kiedy uruchomić

- **PO** `/requesting-code-review` i poprawkach kodu (krok 5 cyklu SDD w CLAUDE.md)
- **PRZED** `/finishing-a-development-branch`
- **Nie uruchamiaj automatycznie** po każdym commicie

## Procedura (planowana)

1. Pobierz diff bieżącej gałęzi vs `main`:
   ```bash
   git diff main...HEAD --name-only
   ```
2. Dla każdego zmienionego pliku sprawdź, która strona wiki ma go w `owns:`:
   ```bash
   grep -l "<path>" docs/llm-wiki/*.md
   ```
3. Dla każdej dotkniętej strony:
   - Pokaż user ścieżkę i sekcje, które prawdopodobnie wymagają aktualizacji
     (na bazie tego, gdzie dany plik jest cytowany w treści)
   - Zaproponuj zmiany jako diff (przed/po)
   - **Tylko propozycja** — nie wykonuj zapisu bez akceptacji
4. Jeśli zmiana w kodzie nie pasuje do żadnej strony — zapytaj:
   "Czy potrzebujemy nowej strony w `docs/llm-wiki/` dla tego komponentu? (y/n/skip)"
   - `y` → utwórz szkielet strony z frontmatter + sekcje placeholder
   - `n` → ignoruj (zmiana nie wymaga dokumentacji)
   - `skip` → flag jako TODO w nowym wpisie `_meta/log.md`
5. Po akceptacji zmian:
   - Zaktualizuj `last_verified_commit: <HEAD-SHA>` w frontmatter dotkniętych stron
   - Zaktualizuj `last_updated: YYYY-MM-DD`
6. Dopisz wpis do `docs/llm-wiki/_meta/log.md`:
   ```markdown
   ## [YYYY-MM-DD HH:MM] wiki-ingest | <N> stron zaktualizowano (<lista>), <M> stron pominięto
   ```

## Co NIE robi

- Nie modyfikuje wiki bez explicit akceptacji usera per strona
- Nie generuje nowych stron bez pytania
- Nie usuwa stron — tylko flag jako `status: deprecated` w frontmatter
- Nie uruchamia testów / lintu — to robota innych komend

## Po `/wiki-ingest`

Zawsze uruchom `/wiki-lint`:
- Sprawdzi back-refs nowych stron
- Wykryje strony-sieroty jeśli nowa strona nie została podlinkowana z `INDEX.md`
- Zaktualizuje `_meta/log.md` z wynikami lintu (osobny wpis)

## TODO

- [ ] Wybrać format proponowanych zmian (unified diff vs natural language vs both)
- [ ] Heurystyka: kiedy "nowa strona" jest naprawdę potrzebna vs sekcja w istniejącej
- [ ] Integracja z `/wiki-lint` — automatyczne uruchomienie po ingest-owych zmianach
- [ ] Subagent dispatch — żeby diff i analiza nie zaśmiecały głównego kontekstu
- [ ] Obsługa zmiany ADR (deletion / supersedes) — propagacja do stron, które do niej linkują
