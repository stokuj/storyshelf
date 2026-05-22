---
description: Sprawdź spójność docs/llm-wiki/ — drift detection, brakujące linki, nieaktualne strony.
---

# /wiki-lint

Workflow tekstowy (nie skrypt) — Claude wykonuje ręcznie 6 reguł i raportuje.
Tryby: `/wiki-lint` (pełny), `/wiki-lint <slug>` (pojedyncza strona), `/wiki-lint --fix`
(zaproponuj poprawki, czekaj na akceptację przed zapisem).

## Procedura

1. Przeczytaj `docs/llm-wiki/_meta/INDEX.md` → zidentyfikuj wszystkie zarejestrowane strony.
2. Przeczytaj każdą stronę po kolei (frontmatter + treść).
3. Sprawdź 6 reguł:

### Reguły

**R1 — Pliki w `owns:` istnieją w repo.**
Dla każdej ścieżki w `owns:` sprawdź `test -f <path>`. Brak = ERROR.

**R2 — `related_pages:` istnieją i back-reference jest obustronna.**
Jeśli A ma `related_pages: [B]`, to B musi mieć A w `related_pages:`. Brak back-ref = WARN.
Jeśli B w ogóle nie istnieje w `docs/llm-wiki/<B>.md` = ERROR.

**R3 — `last_verified_commit` nie starszy niż HEAD plików w `owns:`.**
Dla każdej strony:
```bash
git log -1 --format=%H -- <owns paths>
```
Jeśli SHA jest nowszy niż `last_verified_commit` w frontmatter → flag jako STALE (WARN).
Wyjątek: `status: wip` — pomijamy regułę.

**R4 — Strony-sieroty.**
Strona nie zalinkowana z `docs/llm-wiki/_meta/INDEX.md` ani z żadnej innej strony przez
`[[slug]]` lub markdown link → ORPHAN (WARN).

**R5 — Wymagane sekcje obecne.**
Każda strona (poza `status: wip`) musi mieć nagłówki:
- `## Co to jest`
- `## Jak działa`
- `## Pułapki`
- `## Pytania, na które ta strona odpowiada`

Brak = ERROR (zalecane też `## Decyzje` i `## Typowe operacje`, ale nie blokujące).

**R6 — Linki `[[slug]]` i markdown linki działają.**
- Każdy `[[slug]]` → musi odpowiadać `docs/llm-wiki/<slug>.md` lub
  `docs/decisions/ADR-<slug>.md`
- Każdy `](relative-path)` → plik musi istnieć (rozwiąż relative path względem strony)

Brak = ERROR.

## Raport

Format wyjścia:
```
# Wiki lint — YYYY-MM-DD HH:MM

✓ R1 owns: paths        N/N stron OK
✗ R3 stale              <strona>.md (last_verified=<sha-old>, HEAD=<sha-new>, diff: <pliki>)
⚠ R4 orphans            (brak | <lista>)
⚠ R2 back-refs          <A>.md → [B] (brak back-ref w <B>.md)

Errors: <N>
Warnings: <M>
```

Po raporcie: **zawsze** dopisz wpis do `docs/llm-wiki/_meta/log.md`:
```markdown
## [YYYY-MM-DD HH:MM] wiki-lint | <N> errors, <M> warnings
```

## Tryb `--fix`

Tam gdzie da się naprawić automatycznie, przygotuj diff i pokaż userowi przed zapisem:
- Brakujące back-refs: dopisanie do `related_pages` (R2)
- Stary `last_verified_commit`: aktualizacja do HEAD **po** ręcznym sprawdzeniu, że treść strony
  faktycznie zgadza się z kodem (nie automatycznie!)

User akceptuje (`y`) lub modyfikuje propozycje. Bez `--fix` lint jest read-only.

## Co NIE robi

- Nie zmienia treści stron bez `--fix` + user confirmation
- Nie sprawdza merytorycznej poprawności (czy "Jak działa" zgadza się z kodem) — to robota
  dla `/wiki-ingest`
- Nie usuwa stron — tylko flag jako STALE
