# Design: Frontend Quality Refactor (Issue #32)

## Overview

Zbiorczy issue dla 3 ostrzeżeń jakości frontendu: redundantny `refreshAuth()`, współdzielony stan `saving` w adminie, zduplikowane bloki `try/catch`.

## 1. Router zawsze odświeża auth, usuń redundantne wywołania

### Problem

`router.beforeEach` wywołuje `refreshAuth()` tylko przy pierwszej nawigacji (`!authState.initialized`), ponieważ `initialized` nigdy nie wraca na `false`:
- `App.vue:38-40` — `onMounted(() => { refreshAuth() })` duplikuje router guard
- `BookDetailView.vue:295`, `ProfileView.vue:112`, `BookshelfView.vue:103`, `SettingsView.vue:113` — każdy widok osobno woła `refreshAuth()` w swojej funkcji ładującej

### Rozwiązanie

**`router.js:82-85`** — usuń warunek `!authState.initialized`:
```js
// przed:
if (!authState.initialized) {
  await refreshAuth()
}

// po:
await refreshAuth()
```

Router zawsze odświeża sesję przed każdą nawigacją. Usuń wszystkie redundantne wywołania:
- `App.vue`: usuń `onMounted(() => { refreshAuth() })`, import `refreshAuth` i `onMounted` (jeśli nieużywany)
- `BookDetailView.vue`: usuń `await refreshAuth()` z `loadDetails()`, import
- `ProfileView.vue`: usuń `await refreshAuth()` z `loadProfile()`, import
- `BookshelfView.vue`: usuń `await refreshAuth()` z `loadBookshelf()`, import
- `SettingsView.vue`: usuń `await refreshAuth()` z `loadSettings()`, import

### Efekt

Każda nawigacja = jedna sesja refresh. Zero powielania. Widoki używają `authState` zależnego od routera.

## 2. Zastąp współdzielony `saving` per-row stanem

### Problem

`AdminBooksView.vue:160`, `AdminAuthorsView.vue:99`, `AdminSeriesView.vue:110` — `const saving = ref(false)` współdzielony przez wszystkie wiersze `v-for`. Zapisanie jednego wiersza blokuje wszystkie.

### Rozwiązanie

Zamień `saving = ref(false)` na `savingRowId = ref(null)`:

```js
// przed:
const saving = ref(false)

// po:
const savingRowId = ref(null)
```

Logika per-operacja:
- **create** (nowy element, nie w v-for): `savingRowId.value = 'create'`
- **save/edit** (istniejący element): `savingRowId.value = itemId`
- **remove**: `savingRowId.value = itemId`
- W `finally`: `savingRowId.value = null`

Template (przykład AdminBooksView):
```html
<!-- przed: -->
<button :disabled="saving">Zapisz</button>

<!-- po: -->
<button :disabled="savingRowId !== null">Zapisz</button>
```

Przyciski per-row mogą dodatkowo używać `savingRowId === book.id` zamiast `!== null` dla precyzyjniejszego UI (opcjonalnie).

### Dotknięte pliki

- `frontend/src/views/admin/AdminBooksView.vue`
- `frontend/src/views/admin/AdminAuthorsView.vue`
- `frontend/src/views/admin/AdminSeriesView.vue`

## 3. `useAsyncState()` composable

### Problem

31 bloków `try/catch` w 10 plikach kopiuje ten sam pattern:
```js
const loading = ref(true)
const error = ref('')

try { ... }
catch (err) { error.value = err instanceof Error ? err.message : 'fallback' }
finally { loading.value = false }
```

### Rozwiązanie

Nowy plik: `frontend/src/composables/useAsyncState.js`

```js
import { ref } from 'vue'

export function useAsyncState() {
  const loading = ref(false)
  const error = ref('')
  const message = ref('')

  function clearFeedback() {
    error.value = ''
    message.value = ''
  }

  async function execute(fn, options = {}) {
    loading.value = true
    error.value = ''
    message.value = ''

    try {
      return await fn()
    } catch (err) {
      error.value = err instanceof Error ? err.message : options.fallback || 'Wystąpił błąd.'
      throw err
    } finally {
      loading.value = false
    }
  }

  return { loading, error, message, execute, clearFeedback }
}
```

### Refaktor widoków

Każdy widok z try/catch przechodzi na:

```js
import { useAsyncState } from '../composables/useAsyncState'

const { loading, error, message, execute, clearFeedback } = useAsyncState()

async function loadData() {
  await execute(async () => {
    data.value = await fetchSomething()
  }, { fallback: 'Nie udało się pobrać danych.' })
}
```

Widoki z wieloma operacjami async (np. BookDetailView z 5 różnymi try/catch) używają jednej instancji `useAsyncState()` — `execute` czyści błędy przed każdą akcją, loading jest per-wywolanie.

### Widoki refaktorowane

| Plik | Operacje async |
|------|---------------|
| `HomeView.vue` | `loadBooks` |
| `LoginView.vue` | `submitLogin` |
| `RegisterView.vue` | `submitRegister` |
| `BookDetailView.vue` | `loadDetails`, `addShelfEntry`, `changeShelfStatus`, `changeShelfStatusByValue`, `removeShelfEntry`, `submitReview` |
| `ProfileView.vue` | `loadProfile`, `toggleFollow` |
| `BookshelfView.vue` | `loadBookshelf`, `changeStatus`, `removeEntry` |
| `SettingsView.vue` | `loadSettings`, `saveSettings`, `toggleVisibility` |
| `AdminBooksView.vue` | `loadBooks`, `createBook`, `saveBook`, `removeBook`, `uploadContent`, `clearContent` |
| `AdminAuthorsView.vue` | `loadAuthors`, `createAuthor`, `saveAuthor`, `removeAuthor` |
| `AdminSeriesView.vue` | `loadSeries`, `createSeries`, `saveSeries`, `removeSeries` |

## Pliki zmieniane

| Plik | Zmiana |
|------|--------|
| `frontend/src/router.js` | Zawsze `refreshAuth()` w beforeEach |
| `frontend/src/App.vue` | -refreshAuth z onMounted |
| `frontend/src/composables/useAsyncState.js` | **Nowy plik** |
| `frontend/src/views/HomeView.vue` | useAsyncState |
| `frontend/src/views/LoginView.vue` | useAsyncState |
| `frontend/src/views/RegisterView.vue` | useAsyncState |
| `frontend/src/views/BookDetailView.vue` | -refreshAuth + useAsyncState |
| `frontend/src/views/ProfileView.vue` | -refreshAuth + useAsyncState |
| `frontend/src/views/BookshelfView.vue` | -refreshAuth + useAsyncState |
| `frontend/src/views/SettingsView.vue` | -refreshAuth + useAsyncState |
| `frontend/src/views/admin/AdminBooksView.vue` | saving→savingRowId + useAsyncState |
| `frontend/src/views/admin/AdminAuthorsView.vue` | saving→savingRowId + useAsyncState |
| `frontend/src/views/admin/AdminSeriesView.vue` | saving→savingRowId + useAsyncState |

## Weryfikacja

- `npm run build` — frontend kompiluje się bez błędów
- `npm run lint` — zero warningów
- Ręczne sprawdzenie: auth działa na wszystkich ścieżkach, przyciski admin nie blokują się wzajemnie, errory wyświetlają poprawne komunikaty
