# Spike #94 — Agent: tytuł → Strona OKF

> Spike (throwaway). Skrypt: `backend-django/scripts/spike_okf_page.py` — usunięty w #107.

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

1. **Tak — tanie modele wystarczają do formatu.** Surowy Markdown jest OK; structured output/JSON niepotrzebny na tym etapie. Domyślny model: `openai/gpt-6-luna` (patrz [Podsumowanie 5 modeli](#podsumowanie-5-modeli)).
2. **Backend stempluje `generated` (`by`, `at`) i `type`**, nie model. Model zwraca resztę; nadpisujemy te pola po parsowaniu. Tak samo **slugi Ścieżek** (Odnośniki) — slugify w backendzie z nazwy, nie z odpowiedzi modelu.
3. **Generowanie tylko async (Celery)** — 7–60 s (GLM: do 10 min) wyklucza synchroniczne żądanie HTTP. UI potrzebuje stanu „generuję…”. Task potrzebuje twardego limitu czasu całego wywołania i `max_tokens` (timeout `urlopen` dotyczy pojedynczej operacji na sockecie, nie całości).
4. **Limit Wzmianek w prompcie** (np. ≤10 Postaci, ≤6 Miejsc) i tworzenie Stron Postaci/Miejsc leniwie, nie wszystkich naraz.
5. **Halucynacje = osobny problem do M3**: ugruntowanie w Źródłach (np. Wikipedia jako kontekst w prompcie) — wtedy wrócić do `sources`. Do czasu Weryfikacji Strona jest niezweryfikowana, co model już przewiduje.

## Porównanie: `stealth/space-bunny-alpha`

Ten sam prompt i walidacja (`SPIKE_MODEL=stealth/space-bunny-alpha`). Model anonimowy, darmowy (0 $), 1M kontekstu; stealth — prompty mogą być logowane przez dostawcę.

| # | Prośba | Walidacja | Latencja | Tokeny in/out | Wzmianki |
|---|---|---|---|---|---|
| 1 | Dodaj książkę „Ostatnie życzenie” | ❌ `author: ""` | 17,5 s | 452/1140 | 0 |
| 2 | Dodaj książkę „Lalka” | ✅ | 40,5 s | 449/2844 | 14 |
| 3 | Dodaj książkę „Solaris” | ✅ | 40,4 s | 448/2805 | 7 |
| 4 | Add the book “Dune” | ✅ | 37,5 s | 446/2972 | 20 |
| 5 | Add the book “The Hobbit” | ✅ | 19,1 s | 446/1716 | 21 |

- **„Ostatnie życzenie”: nie rozpoznał książki** → pusty Szablon (zgodnie z instrukcją „nie znasz — zwróć puste sekcje”). DeepSeek znał ją bez problemu.
- **Poważna halucynacja w „Solaris”**: Harey (zmarła żona Kelvina) zamieniona w „Annę Kelvin, córkę Kelvina”; Kelvin nazwany „Krzysztof” (w książce: Kris).
- **1/62 Odnośnik z nie-ASCII slugiem** (`krakowskie-przedmieście--lalka`) — slug trzeba generować w backendzie, nie ufać modelowi.
- `generated.at` 5/5 skopiowany z przykładu w prompcie — ten sam problem co DeepSeek.

**Wniosek:** format porównywalny, wiedza o polskiej literaturze wyraźnie słabsza niż `deepseek-v4.1-flash`. Darmowy, ale stealth (niestabilna dostępność, logowanie promptów) — nie nadaje się jako domyślny Agent.

## Porównanie: `openai/gpt-6-luna`, `z-ai/glm-5.3-flash`, `qwen/qwen3.8-27b`

Ten sam prompt i walidacja. Wszystkie trzy: walidacja **5/5**.

| Model | Latencja | Śr. koszt / Stronę | Wzmianki | Odnośniki | `generated.at` |
|---|---|---|---|---|---|
| `openai/gpt-6-luna` | 7–16 s | 0,0006 $ | 7–13 | 48/48 OK | 5/5 `2025-03-08` (data z wiedzy modelu) |
| `z-ai/glm-5.3-flash` | 34–47 s; „Lalka” **618 s** | 0,0053 $ (bez „Lalki” 0,0013 $) | 9–29 | 92/92 wzorzec OK, ale 15× zły slug książki `ostatnie-zycenie` | 5/5 przykład z promptu |
| `qwen/qwen3.8-27b` | 12–44 s | 0,0111 $ | 6–11 | 44/44 OK | 4 różne zmyślone daty; 1× w cudzysłowie |

Fakty (sprawdzone ręcznie na „Ostatnim życzeniu” i „Solaris”):

- **GPT-6 Luna — poprawne.** Kris Kelvin, Harey, Gibarian, Renfri/Blaviken, Rinde. Treść oszczędna (krótkie streszczenie, mniej Wzmianek). Drobne usterki językowe: cyrylickie „е” w „związanе”, „przybyszyni”.
- **GLM-5.3 Flash — najbogatsze, ale niechlujne.** Najlepsze „Solaris” ze wszystkich modeli. W „Ostatnim życzeniu” „Wieczny Ogień” z „Miecza przeznaczenia” i „Dolna Posada” zamiast Ellander; literówki i wtrącenia („wiedźminasplata”, „Gerolata”, „REFLEKSJA”, ang. „witness”). „Lalka”: 42 147 tokenów wyjścia (runaway reasoning) przy stronie 8,6 KB.
- **Qwen3.8 27B — „Solaris” całkowicie zmyślone** (Christoph Bary, Gunny, Snow, Rheinhart). „Ostatnie życzenie” ogólnikowe, z błędnym Kaedwen. Najdroższy (do 7333 tokenów wyjścia). Odpowiedź zaczyna się od pustych linii.

## Podsumowanie 5 modeli

| Model | Format | Fakty (PL) | Koszt / Stronę | Latencja | Werdykt |
|---|---|---|---|---|---|
| `openai/gpt-6-luna` | 5/5 | ✅ poprawne, oszczędne | 0,0006 $ | 7–16 s | **Rekomendacja** |
| `deepseek/deepseek-v4.1-flash` | 5/5 | ⚠️ bogate, miesza tomy cyklu | 0,0013 $ | 22–64 s | Alternatywa (więcej treści) |
| `z-ai/glm-5.3-flash` | 5/5 | ⚠️ bogate, literówki, zły slug | 0,0013–0,021 $ | 34–618 s | Nie — nieprzewidywalny czas/koszt |
| `qwen/qwen3.8-27b` | 5/5 | ❌ zmyślone „Solaris” | 0,0111 $ | 12–44 s | Nie |
| `stealth/space-bunny-alpha` | 4/5 | ❌ nie zna „Ostatniego życzenia”, zmyślone „Solaris” | 0 $ | 17–41 s | Nie |

Walidacja formatu nie odróżnia modeli (4–5/5 wszędzie) — różnią je fakty, koszt i przewidywalność. Ograniczenie: 1 przebieg na tytuł, fakty sprawdzone ręcznie na 2 książkach.

## Otwarte

- `infra/.env` ma `OPENROUTER_MODEL=deepseek/deepseek-v4-pro`, a `base.py` domyślnie `anthropic/claude-3.5-haiku` — ujednolicić przy M3.
- Nie mierzono stabilności (1 przebieg na tytuł) ani książek nieznanych modelowi.
