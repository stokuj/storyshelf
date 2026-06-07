# M14 — Typed Character Relations (design)

> Ulepszenie M13. Zastępuje wolny tekst `CharacterRelation.label` kontrolowanym
> słownikiem typów relacji, koloruje ego-graf wg grup i poprawia render dla
> wielu relacji na parę postaci.

## Problem

M13 trzyma relację jako `CharacterRelation.label = CharField(max_length=120)` —
wolny tekst od LLM. Konsekwencje:

- Brak spójności między książkami ("mentor" vs "teacher" vs "mistrz").
- Graf nie ma koloru, legendy ani struktury — surowy tekst na krawędzi.
- Naiwny render (`relations.map`) rysuje **jeden węzeł na wpis relacji**, więc
  para z dwiema relacjami pokazuje tę samą postać dwa razy.

## Cel

Kontrolowany słownik ~20 typów w 7 grupach, kolorowanie krawędzi wg grupy,
jeden węzeł na postać z kolorowymi „pigułkami" typów. Wielokrotność relacji na
parę dozwolona.

## Decyzje (z brainstormingu)

| Decyzja | Ustalenie |
|---|---|
| Rozmiar taksonomii | ~20 typów / 7 grup (z `OTHER`) |
| Kierunek | jednokierunkowo jak M13 (bez liczenia odwrotności) |
| Wielokrotność | tak — unikalne `(from, to, type)` |
| Free-text `label` | usunięty całkowicie |

## Taksonomia

Definicja w nowym module `characters/relations.py`. `RelationType` jako
`models.TextChoices`; `RELATION_GROUPS` mapuje typ → grupa. **Jedno źródło
prawdy**: grupa wyliczana z mapy, nie trzymana w bazie.

| Grupa | Typy |
|---|---|
| `family` | `PARENT`, `CHILD`, `SIBLING`, `SPOUSE`, `RELATIVE` |
| `romance` | `LOVER`, `EX_PARTNER` |
| `friendship` | `FRIEND`, `ALLY` |
| `mentorship` | `MENTOR`, `MENTEE` |
| `power` | `MASTER`, `SERVANT`, `LEADER`, `FOLLOWER` |
| `conflict` | `ENEMY`, `RIVAL` |
| `other` | `COLLEAGUE`, `ACQUAINTANCE`, `OTHER` |

**Semantyka kierunku:** `relation_type` opisuje rolę `to_character` względem
`from_character`. Krawędź `Paul → Leto` z typem `PARENT` czyta się „Leto jest
rodzicem Paula". Na podstronie postaci (ego-graf) środek = `from`, szprychy =
inne postacie opisane ich rolą względem środka. Typy symetryczne (`SIBLING`,
`SPOUSE`, `FRIEND`, `ALLY`, `ENEMY`, `RIVAL`, `LOVER`, `EX_PARTNER`,
`RELATIVE`, `COLLEAGUE`, `ACQUAINTANCE`, `OTHER`) — kierunek bez znaczenia.
Asymetryczne pary: `PARENT`/`CHILD`, `MENTOR`/`MENTEE`, `MASTER`/`SERVANT`,
`LEADER`/`FOLLOWER`.

Funkcja `relation_group(relation_type: str) -> str` zwraca grupę; nieznany typ → `"other"`.

## Model (`characters/models.py`)

`CharacterRelation`:

- usuń `label`,
- dodaj `relation_type = models.CharField(max_length=20, choices=RelationType.choices)`,
- `UniqueConstraint(fields=["from_character", "to_character", "relation_type"], name="unique_relation_type_per_pair")`,
- `@property group(self) -> str: return relation_group(self.relation_type)`,
- `__str__`: `f"{from} → {to} ({relation_type})"`.

Migracja `characters/migrations/0002_*` (generowana przez `makemigrations`; nie
edytujemy 0001). Dane są regenerowalne (delete-and-replace przez LLM), więc
utrata starych `label` jest akceptowalna. W dev `migrate` na żywą dev-DB
(`DATABASE_URL=postgres://postgres:CHANGE_ME@localhost:5432/...`), bo kontener
przeładuje kod, ale nie schema.

## AI (`characters/ai.py`)

- Kształt relacji w JSON: `{"from": name, "to": name, "type": RELATION_TYPE}`.
- Lista dozwolonych typów wstrzykiwana do promptu z `RelationType.values`
  (jedno źródło prawdy — dodanie typu w enumie automatycznie trafia do promptu).
- Zdanie o semantyce kierunku: „`type` is the role of `to` relative to `from`
  (e.g. from=child, to=parent → PARENT)".
- „If unsure which type fits, use OTHER."
- `data.setdefault("relations", [])` bez zmian.

## Walidacja i zapis (`characters/services.py`)

- Zbuduj zbiór dozwolonych wartości z `RelationType.values`.
- Dla każdej relacji: `raw = (rel.get("type") or "").strip()`; mapuj
  case-insensitive na enum; **nieznane lub puste → `RelationType.OTHER`**
  (nigdy nie pada — `OTHER` to zawsze prawidłowa wartość).
- Dedup na `(id(source), id(target), relation_type)`.
- Zapis `relation_type` zamiast `label`.

## API (`characters/serializers.py`)

`CharacterRelationSerializer` zwraca:

| Pole | Źródło |
|---|---|
| `to_slug` | `to_character.slug` |
| `to_name` | `to_character.name` |
| `type` | `relation_type` |
| `type_display` | `get_relation_type_display()` |
| `group` | `obj.group` |

`CharacterDetailSerializer.relations` typowane przez
`@extend_schema_field(CharacterRelationSerializer(many=True))` (bez zmian poza
nowym kształtem). OpenAPI regenerowane (`make regenerate-openapi`), kontrakt
test `config/tests/test_openapi_schema.py`.

## Frontend

`svelte-frontend/src/lib/types/character.ts` — `CharacterRelation`:
`label` → `type: string`, `type_display: string`, `group: string`.

`svelte-frontend/src/lib/components/character/RelationGraph.svelte`:

- **Grupowanie po `to_slug`**: z `relations` zbuduj listę unikalnych postaci,
  każda z tablicą `{ type_display, group }`. Jeden węzeł na postać.
- Pozycje węzłów na okręgu jak dziś (liczone po liczbie postaci, nie relacji).
- Każda relacja jako pigułka (rounded rect + biały tekst `type_display`),
  kolor tła = `groupColor(group)`. Wiele pigułek na krawędzi układanych pionowo
  przy środku krawędzi.
- `groupColor`: mapa 7 grup → kolor (jak na zatwierdzonym mockupie):
  `family #d97706`, `romance #db2777`, `friendship #16a34a`,
  `mentorship #2563eb`, `power #7c3aed`, `conflict #dc2626`, `other #6b7280`.
  Fallback dla nieznanej grupy → kolor `other`.
- Klucz `{#each}` na `to_slug` (węzły) i `${to_slug}::${type}` (pigułki).
- Linia łącząca neutralna (`#8884`), jak dziś.
- Mała legenda pod SVG: nazwa grupy + próbka koloru, tylko dla grup obecnych w
  bieżącym grafie.

## Testy

**Backend** (`DJANGO_ENV=dev`):

- `relations.py`: `relation_group` zwraca poprawną grupę dla reprezentanta każdej
  grupy; nieznany typ → `"other"`.
- `services`: typ spoza enuma → `OTHER`; pusty typ → `OTHER`; znany typ
  (case-insensitive, np. `"parent"`/`"PARENT"`) → `PARENT`; dedup `(from,to,type)`;
  ta sama para z dwoma różnymi typami → dwie relacje.
- `ai`: `_build_prompt` zawiera reprezentatywne typy (np. `PARENT`, `OTHER`).
- model: `UniqueConstraint` blokuje duplikat `(from,to,type)`.
- aktualizacja istniejących testów odnoszących się do `label`:
  `test_services.py`, `test_ai.py`, `test_serializers.py`, `test_tasks.py`
  (fake data: `"label"` → `"type"`).

**Frontend:** `npm run check` (svelte-check + TS), `npm run lint`.

**Kontrakt:** OpenAPI snapshot zregenerowany i zgodny.

## Poza zakresem (YAGNI)

- Odwrotności / dwukierunkowy render relacji.
- Filtr krawędzi po grupie.
- Pole `note` / wolny tekst obok typu.
- Edycja relacji w UI.
- Migracja danych starych `label` na typy (dane regenerowalne).

## Gałąź

`feat/m14-typed-relations`. Konwencjonalne commity, bez squasha. Spec + plan
usuwane osobnym commitem przed PR (wzorzec milestone'ów).
