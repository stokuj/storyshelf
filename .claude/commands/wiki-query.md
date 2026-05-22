---
description: Odpowiedz na pytanie o system StoryShelf, używając docs/llm-wiki/ jako źródła.
---

# /wiki-query

**Status: SZKIELET.** Pełna implementacja gdy ręczne korzystanie z wiki wejdzie w nawyk
(zgodnie z regułą "nie automatyzuj rzeczy, których jeszcze nie robisz ręcznie").

## Procedura (planowana)

1. Pobierz pytanie użytkownika (argumenty komendy).
2. Przeczytaj `docs/llm-wiki/_meta/INDEX.md` → lista stron + ich one-liner descriptions.
3. **Match wstępny**: dla każdej strony przeczytaj sekcję `## Pytania, na które ta strona
   odpowiada`. Wybierz 1-3 strony, których pytania najbliżej pasują semantycznie do zapytania
   usera.
4. Przeczytaj wybrane strony w całości.
5. Odpowiedz, cytując źródła w formacie `[[slug]]#sekcja` (np. `[[auth-flow]]#Pułapki`).
6. Jeśli żadna strona nie pasuje — powiedz wprost: "wiki nie zawiera odpowiedzi na to pytanie,
   spróbuj sprawdzić kod w <relevant directory>".

## Kiedy zaimplementować pełną wersję

- Gdy wiki ma ≥10 stron (poniżej tej liczby — bezpośrednie czytanie INDEX szybsze niż routing)
- Gdy zauważysz, że pytasz Claude'a "jak działa X" zamiast wprost otwierać `docs/llm-wiki/<x>.md`
- Gdy `/wiki-lint` zgłasza pełne pokrycie kluczowych komponentów (no orphans, no missing pages)

## TODO

- [ ] Zdefiniować dokładny format outputu (zwięzły 2-3 zdania vs rozszerzony z cytatami)
- [ ] Dodać fallback do grep przez `docs/llm-wiki/`, gdy match po sekcji "Pytania" zawiedzie
- [ ] Rozważyć subagent (`Explore` lub własny) z ograniczonymi narzędziami (Read + Glob), żeby
      nie zaśmiecać głównego kontekstu czytaniem stron
- [ ] Format cytowania: `[[auth-flow]]#Pułapki` vs `[auth-flow → Pułapki]` vs link markdown

## Co NIE robi (nawet po pełnej implementacji)

- Nie modyfikuje wiki — tylko czyta i raportuje
- Nie wnioskuje z kodu, jeśli wiki nie odpowiada — zwraca explicit "brak w wiki"
- Nie loguje queries do `_meta/log.md` (tylko mutacje są logowane)
