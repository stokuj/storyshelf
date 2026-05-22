---
title: API Conventions
last_updated: 2026-05-22
last_verified_commit: 86ea9b0
owns:
  - backend-django/books/serializers.py
  - backend-django/books/urls.py
  - backend-django/books/views.py
  - backend-django/shelf/serializers.py
  - backend-django/reviews/serializers.py
  - backend-django/users/serializers.py
  - backend-django/analysis/models.py
  - frontend/src/api.js
  - frontend/src/composables/useAsyncState.js
depends_on:
  - Django REST Framework
related_pages: [auth-flow, nlp-pipeline, dev-setup]
status: stable
---

## Co to jest

Kontrakt między backendem Django (DRF) a frontendem Vue 3. Definiuje konwencje URL,
formatów payloadu, namingu pól, paginacji i obsługi błędów. Ten plik to **jedno źródło
prawdy** dla integracji — przy zmianie konwencji aktualizuj go tu, nie w osobnych
plikach per app.

## Jak działa

**URL conventions:**
- Wszystkie ścieżki mają trailing slash: `/api/books/`, `/api/books/42/`
- `frontend/src/api.js` automatycznie dodaje `/` jeśli brakuje przed query string

**Naming pól:**
- Backend: snake_case (Python style)
- Frontend: oczekuje camelCase
- Mapping w DRF serializerach: `mentionCount = serializers.IntegerField(source="mention_count")`

**Paginacja:**
- Frontend oczekuje **płaskich tablic** (`[{...}, {...}]`), nie `{count, results}`
- Wszystkie listowe endpointy konsumowane przez frontend mają `pagination_class = None`:
  books list, shelf, reviews, characters, relations, followers, following

**Stan async (frontend):**
- `useAsyncState` w `frontend/src/composables/useAsyncState.js`:
  - `execute(fn, { timeout: ms, fallback })`
  - default timeout: 15000 ms
  - przy timeout: rzuca błąd `'Przekroczono czas oczekiwania.'`
- Wszystkie 7 views używają `useAsyncState` zamiast ręcznego try/catch

**Error response:**
- Domyślny format DRF: `{"detail": "..."}` lub `{"<field>": ["<error>"]}`
- Frontend `AlertMessage.vue` renderuje `error.message` lub `error.detail`

## Decyzje

- camelCase mapping zamiast globalnego `JSON_CAMEL_CASE_RENDERER`: świadoma kontrola per pole,
  unika niezamierzonego renamowania pól wewnętrznych Django (`pk`, `id`)
- Brak paginacji na listowych endpointach: skala projektu (single-tenant, <1000 książek per user)
  nie wymaga paginacji; flat array upraszcza frontend

## Typowe operacje

**Dodanie nowego pola z mappingiem snake → camel:**
```python
# backend-django/books/serializers.py
class BookSerializer(serializers.ModelSerializer):
    avgRating = serializers.DecimalField(source="avg_rating", max_digits=3, decimal_places=2, read_only=True)
    ratingsCount = serializers.IntegerField(source="ratings_count", read_only=True)

    class Meta:
        model = Book
        fields = ["id", "title", "avgRating", "ratingsCount", ...]
```

**Nowy listowy endpoint bez paginacji:**
```python
# backend-django/<app>/views.py
class MyListView(generics.ListAPIView):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    pagination_class = None   # WAŻNE: frontend oczekuje flat array
```

**Fetch z frontendu (z timeout):**
```javascript
import { useAsyncState } from '@/composables/useAsyncState'
import { listBooks } from '@/api'

const { data, error, loading, execute } = useAsyncState()
execute(() => listBooks(), { timeout: 10000 })
```

## Pułapki

- **Trailing slash**: brak slash = redirect (DRF wymaga slash dla DefaultRouter). `api.js`
  dodaje slash automatycznie, ale przy ręcznych fetchach pamiętaj.
- **`avg_rating` vs `rating`**: `BookSerializer` wystawia `avg_rating` (snake — frontend tu nie
  używa mappingu, bo nazwa pola Django jest już taka). Frontend musi pisać `book.avg_rating`.
  `book.rating` jest `undefined` i renderuje się jako pusty string.
- **`relation_type` vs `relation`**: `CharacterRelationSerializer` wystawia `relation_type`.
  Frontend musi używać `rel.relation_type`. Brak pola `evidence` w odpowiedzi.
- **`pagination_class = None`**: jeśli zapomnisz, frontend dostanie `{count, next, previous, results}`
  i Vue Template wyrenderuje "[object Object]".
- **camelCase tylko gdzie zdefiniowane**: każdy serializer ustala mapping per pole. Brak globalnej
  konwersji — pole bez explicit `source=` zachowa nazwę Django (snake).
- **useAsyncState timeout**: 15s domyślnie. Dla długich operacji (np. NLP triggered manually)
  zwiększ: `execute(fn, { timeout: 60000 })`.
- **Frontend strings są po polsku** — `AlertMessage` używa polskich tekstów (`'Wystąpił błąd...'`,
  `'Przekroczono czas oczekiwania.'`). Nie tłumacz ich na inglish.

## Pytania, na które ta strona odpowiada

- Czemu mój response nie wyświetla się we frontendzie?
- Jak dodać nowy endpoint zwracający listę?
- Czemu `book.rating` jest undefined?
- Jak działa silent refresh dla JWT? (patrz [[auth-flow]])
- Jak mapować pole snake_case na camelCase?
- Czemu fetch działa w Postmanie ale nie we frontendzie?
- Jak ustawić timeout dla wolnego endpointa?
- Czemu paginacja DRF łamie listę książek?
- Jakie pola wystawia CharacterRelationSerializer?
