# Spike #94 — Agent: tytuł → Strona OKF

> Spike (throwaway). Skrypt: `backend-django/scripts/spike_okf_page.py` — do wyrzucenia przed M3.

## Pytanie

Czy tani model przez OpenRouter, mając tylko prośbę Usera z tytułem, oddaje Stronę książki zgodną z OKF v0.2 i Szablonem? Ile to kosztuje i trwa?

## Setup

- Model: `deepseek/deepseek-v4.1-flash` (0,30 $ / 1,20 $ za 1M tokenów in/out), jedno wywołanie, bez retry, bez structured output — odpowiedź to surowy Markdown.
- Prompt: frontmatter (`type`, `title`, `description`, `author`, `generated`), 4 sekcje Szablonu (PL: Streszczenie / Postacie / Miejsca / Wątki i motywy; EN: Summary / Characters / Places / Themes), Wzmianki jako `- [Imię](/characters/<slug>--<book>.md) — rola`. Język = język prośby.
- Walidacja: YAML się parsuje, `type: book`, `title`/`description`/`author` niepuste, `generated.by` + `generated.at` w ISO 8601, nagłówki dokładnie w kolejności Szablonu. **Bez `sources`** (decyzja: na razie nie testujemy).

## Wyniki

| # | Prośba | Walidacja | Latencja | Tokeny in/out | Koszt $ | Wzmianki |
|---|---|---|---|---|---|---|
| 1 | Dodaj książkę „Ostatnie życzenie” | ✅ | 31,6 s | 336/3493 | 0,0021 | 22 |
| 2 | Dodaj książkę „Lalka” | ✅ | 22,2 s | 334/2207 | 0,0013 | 17 |
| 3 | Dodaj książkę „Solaris” | ✅ | 28,0 s | 333/1650 | 0,0010 | 8 |
| 4 | Add the book “Dune” | ✅ | 64,2 s | 332/2550 | 0,0015 | 28 |
| 5 | Add the book “The Hobbit” | ✅ | 24,3 s | 333/1315 | 0,0008 | 19 |

- **Format: 5/5.** Frontmatter, nagłówki Szablonu, język (PL→PL, EN→EN), brak bloków kodu. Wszystkie 94 Odnośniki pasują do `/(characters|places)/<ascii-slug>--<book-slug>.md`.
- **Koszt:** średnio ~0,0013 $ za Stronę (~750 Stron / 1 $).
- **Latencja:** 22–64 s.

## Problemy

1. **`generated.at` jest zmyślone.** 4/5 to skopiowany przykład z promptu (`2026-10-03T12:00:00Z`), Dune ma `2026-02-14T09:30:00Z`. Model nie zna aktualnego czasu.
2. **Fakty mieszają się w obrębie cyklu.** „Ostatnie życzenie” zawiera Istredda, Borcha Trzy Kawki i smoka — to postacie/wątek z „Miecza przeznaczenia”. Format jest poprawny, treść nie. Walidacja formatu tego nie złapie.
3. **Liczba Wzmianek bez limitu: 8–28.** W M3 każda Wzmianka = osobna Strona Postaci/Miejsca, więc koszt Generowania rośnie liniowo z tą liczbą.
4. Drobne: styl listy w „Wątki i motywy” różny między stronami (`- X — y` vs `- **X**: y`) — nie narusza Szablonu.

## Rekomendacja dla M3

1. **Tak, ten model wystarcza do formatu.** Surowy Markdown jest OK; structured output/JSON niepotrzebny na tym etapie.
2. **Backend stempluje `generated` (`by`, `at`) i `type`**, nie model. Model zwraca resztę; nadpisujemy te pola po parsowaniu.
3. **Generowanie tylko async (Celery)** — 20–60 s wyklucza synchroniczne żądanie HTTP. UI potrzebuje stanu „generuję…”.
4. **Limit Wzmianek w prompcie** (np. ≤10 Postaci, ≤6 Miejsc) i tworzenie Stron Postaci/Miejsc leniwie, nie wszystkich naraz.
5. **Halucynacje = osobny problem do M3**: ugruntowanie w Źródłach (np. Wikipedia jako kontekst w prompcie) — wtedy wrócić do `sources`. Do czasu Weryfikacji Strona jest niezweryfikowana, co model już przewiduje.

## Otwarte

- `infra/.env` ma `OPENROUTER_MODEL=deepseek/deepseek-v4-pro`, a `base.py` domyślnie `anthropic/claude-3.5-haiku` — ujednolicić przy M3.
- Nie mierzono stabilności (1 przebieg na tytuł) ani książek nieznanych modelowi.
