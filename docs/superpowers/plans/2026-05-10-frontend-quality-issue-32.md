# Frontend Quality Refactor (Issue #32) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wyeliminować 3 code smells: redundantny `refreshAuth()`, współdzielony `saving` stan w adminie, 31 zduplikowanych `try/catch` bloków.

**Architecture:** `useAsyncState()` composable zastępuje ręczne `try/catch` + `loading/error` we wszystkich 10 widokach. Router zawsze odświeża auth, widoki i App.vue nie powielają tej logiki. Adminowe `saving` przechodzi na `savingRowId` per-wiersz.

**Tech Stack:** Vue 3 (Composition API `<script setup>`), Vue Router, Vite

---

### Task 1: Create `useAsyncState` composable

**Files:**
- Create: `frontend/src/composables/useAsyncState.js`

- [ ] **Step 1: Stwórz katalog composables**

```bash
mkdir -p frontend/src/composables
```

- [ ] **Step 2: Napisz composable**

Zawartość `frontend/src/composables/useAsyncState.js`:

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

- [ ] **Step 3: Commit**

```bash
git add frontend/src/composables/useAsyncState.js
git commit -m "feat: add useAsyncState composable for try/catch dedup (issue #32)"
```

---

### Task 2: Router always refreshAuth

**Files:**
- Modify: `frontend/src/router.js:82-85`

- [ ] **Step 1: Usuń warunek initialized z beforeEach**

Zmień blok `beforeEach` w `frontend/src/router.js` (linie 82-85):

```js
// przed:
router.beforeEach(async (to) => {
  if (!authState.initialized) {
    await refreshAuth()
  }

// po:
router.beforeEach(async (to) => {
  await refreshAuth()
```

Usuń tylko warunek `if (!authState.initialized) {` i zamykający `}`, pozostaw `await refreshAuth()` na tym samym poziomie wcięcia.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/router.js
git commit -m "refactor: always refresh auth in router beforeEach (issue #32)"
```

---

### Task 3: Remove refreshAuth from App.vue

**Files:**
- Modify: `frontend/src/App.vue:26-40`

- [ ] **Step 1: Usuń refreshAuth i onMounted**

W `frontend/src/App.vue`:

**Script setup — usuń importy i funkcję:**
```js
// usuń te linie:
import { onMounted } from 'vue'
import { authState, refreshAuth, signOut } from './auth'

// dodaj ten import zamiast:
import { authState, signOut } from './auth'
```

**Usuń blok onMounted (linie 38-40):**
```js
// usuń:
onMounted(() => {
  refreshAuth()
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.vue
git commit -m "refactor: remove redundant refreshAuth from App.vue (issue #32)"
```

---

### Task 4: Refactor HomeView, LoginView, RegisterView

**Files:**
- Modify: `frontend/src/views/HomeView.vue`
- Modify: `frontend/src/views/LoginView.vue`
- Modify: `frontend/src/views/RegisterView.vue`

- [ ] **Step 1: HomeView — zastąp try/catch useAsyncState**

W `frontend/src/views/HomeView.vue`:

Dodaj import:
```js
import { useAsyncState } from '../composables/useAsyncState'
```

Zamień `loading`, `error`, `loadBooks`:

```js
// przed:
const loading = ref(true)
const error = ref('')

async function loadBooks() {
  const query = typeof route.query.q === 'string' ? route.query.q : ''
  loading.value = true
  error.value = ''
  try {
    books.value = await fetchBooks(query)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się pobrać książek.'
  } finally {
    loading.value = false
  }
}

// po:
const { loading, error, execute } = useAsyncState()

async function loadBooks() {
  const query = typeof route.query.q === 'string' ? route.query.q : ''
  await execute(async () => {
    books.value = await fetchBooks(query)
  }, { fallback: 'Nie udało się pobrać książek.' })
}
```

- [ ] **Step 2: LoginView — zastąp try/catch useAsyncState**

W `frontend/src/views/LoginView.vue`:

Dodaj import:
```js
import { useAsyncState } from '../composables/useAsyncState'
```

Zamień `loading`, `error`, `submitLogin`:

```js
// przed:
const loading = ref(false)
const error = ref('')

async function submitLogin() {
  loading.value = true
  error.value = ''
  try {
    await loginUser({ username: form.email, password: form.password })
    await refreshAuth()
    const nextPath = typeof route.query.next === 'string' ? route.query.next : '/'
    router.push(nextPath)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zalogować.'
  } finally {
    loading.value = false
  }
}

// po:
const { loading, error, execute } = useAsyncState()

async function submitLogin() {
  const ok = await execute(async () => {
    await loginUser({ username: form.email, password: form.password })
    return true
  }, { fallback: 'Nie udało się zalogować.' })
  if (!ok) return
  await refreshAuth()
  const nextPath = typeof route.query.next === 'string' ? route.query.next : '/'
  router.push(nextPath)
}
```

- [ ] **Step 3: RegisterView — zastąp try/catch useAsyncState**

W `frontend/src/views/RegisterView.vue`:

Dodaj import:
```js
import { useAsyncState } from '../composables/useAsyncState'
```

Zamień `loading`, `error`, `submitRegister`:

```js
// przed:
const loading = ref(false)
const error = ref('')

async function submitRegister() {
  if (form.password !== confirmPassword.value) {
    error.value = 'Hasła nie są identyczne.'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await registerUser(form)
    router.push('/login?registered=1')
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się utworzyć konta.'
  } finally {
    loading.value = false
  }
}

// po:
const { loading, error, execute } = useAsyncState()

async function submitRegister() {
  if (form.password !== confirmPassword.value) {
    error.value = 'Hasła nie są identyczne.'
    return
  }
  const ok = await execute(async () => {
    await registerUser(form)
    return true
  }, { fallback: 'Nie udało się utworzyć konta.' })
  if (!ok) return
  router.push('/login?registered=1')
}
```

Usuń też nieużywany `ref` z importu jeśli był tylko do `loading`/`error`:
```js
// przed:
import { reactive, ref } from 'vue'
// po (jeśli ref już nieużywany):
import { reactive } from 'vue'
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/HomeView.vue frontend/src/views/LoginView.vue frontend/src/views/RegisterView.vue
git commit -m "refactor: useAsyncState in HomeView, LoginView, RegisterView (issue #32)"
```

---

### Task 5: Refactor BookDetailView

**Files:**
- Modify: `frontend/src/views/BookDetailView.vue`

- [ ] **Step 1: Zastąp try/catch + usuń refreshAuth**

W `frontend/src/views/BookDetailView.vue`:

**Importy:**
```js
// przed:
import { authState, refreshAuth } from '../auth'

// po:
import { authState } from '../auth'
```

Dodaj:
```js
import { useAsyncState } from '../composables/useAsyncState'
```

**Stan — zastąp ręczne refy:**
```js
// przed:
const loading = ref(true)
const error = ref('')
const shelfLoading = ref(false)
const reviewLoading = ref(false)
const reviewError = ref('')
const reviewMessage = ref('')
const randomReviews = ref([])

// po:
const { loading, error, execute } = useAsyncState()
const { loading: shelfLoading, error: shelfError, execute: executeShelf } = useAsyncState()
const { loading: reviewLoading, error: reviewError, message: reviewMessage, execute: executeReview } = useAsyncState()
const randomReviews = ref([])
```

Uwaga: `shelfLoading` i `reviewLoading` inicjują się jako `false` (domyślnie w composable). Dla `loading` który startuje jako `true` na starcie strony, ustaw `loading.value = true` w `onMounted` przed pierwszym `execute`.

**loadDetails (linie 289-309):**
```js
// przed:
async function loadDetails() {
  loading.value = true
  error.value = ''
  try {
    await refreshAuth()
    details.value = await fetchBookDetails(route.params.id)
    randomReviews.value = pickRandomReviews(details.value?.reviews || [], 6)
  } catch (err) {
    const msg = err instanceof Error ? err.message : ''
    if (msg.includes('404') || msg.includes('Not Found') || msg.includes('not found')) {
      details.value = null
    } else {
      error.value = err instanceof Error ? err.message : 'Nie udało się pobrać szczegółów książki.'
    }
    randomReviews.value = []
  } finally {
    loading.value = false
  }
}

// po:
async function loadDetails() {
  loading.value = true
  try {
    const result = await execute(async () => {
      return await fetchBookDetails(route.params.id)
    }, { fallback: 'Nie udało się pobrać szczegółów książki.' })
    if (result) {
      details.value = result
      randomReviews.value = pickRandomReviews(details.value?.reviews || [], 6)
    } else {
      randomReviews.value = []
    }
  } catch {
    // 404 handling — already set by execute fallback, but details stays null
    details.value = null
    randomReviews.value = []
  }
}
```

Uwaga: `BookDetailView` ma specjalną logikę 404. Ponieważ `execute` zwraca `undefined` przy błędzie (throw wewnątrz jest wyłapywany), `result` będzie `undefined` dla błędów. Dla 404 chcemy `details.value = null`, dla innych błędów error jest już ustawiony. Ponieważ nie możemy odróżnić typu błędu wewnątrz `execute`, stosujemy `execute` z fallbackiem i łapiemy wyjątek zewnętrznie tylko do ustawienia `details.value = null`.

**addShelfEntry (linie 311-323):**
```js
// przed:
async function addShelfEntry() {
  shelfLoading.value = true
  error.value = ''
  try {
    details.value.shelfEntry = await addToBookshelf(route.params.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się dodać książki do półki.'
  } finally {
    shelfLoading.value = false
  }
}

// po:
async function addShelfEntry() {
  await executeShelf(async () => {
    details.value.shelfEntry = await addToBookshelf(route.params.id)
  }, { fallback: 'Nie udało się dodać książki do półki.' })
}
```

**changeShelfStatus (linie 325-339):**
```js
// przed:
async function changeShelfStatus(event) {
  shelfLoading.value = true
  error.value = ''
  const previousStatus = details.value?.shelfEntry?.status
  try {
    details.value.shelfEntry = await updateBookshelfStatus(route.params.id, event.target.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zmienić statusu książki.'
    event.target.value = previousStatus
  } finally {
    shelfLoading.value = false
  }
}

// po:
async function changeShelfStatus(event) {
  const previousStatus = details.value?.shelfEntry?.status
  const ok = await executeShelf(async () => {
    details.value.shelfEntry = await updateBookshelfStatus(route.params.id, event.target.value)
    return true
  }, { fallback: 'Nie udało się zmienić statusu książki.' })
  if (!ok) event.target.value = previousStatus
}
```

**changeShelfStatusByValue (linie 341-356):**
```js
// przed:
async function changeShelfStatusByValue(status) {
  shelfLoading.value = true
  error.value = ''
  try {
    if (details.value?.shelfEntry) {
      details.value.shelfEntry = await updateBookshelfStatus(route.params.id, status)
    } else {
      details.value.shelfEntry = await addToBookshelf(route.params.id, status)
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zapisać statusu książki.'
  } finally {
    shelfLoading.value = false
  }
}

// po:
async function changeShelfStatusByValue(status) {
  await executeShelf(async () => {
    if (details.value?.shelfEntry) {
      details.value.shelfEntry = await updateBookshelfStatus(route.params.id, status)
    } else {
      details.value.shelfEntry = await addToBookshelf(route.params.id, status)
    }
  }, { fallback: 'Nie udało się zapisać statusu książki.' })
}
```

**removeShelfEntry (linie 358-371):**
```js
// przed:
async function removeShelfEntry() {
  shelfLoading.value = true
  error.value = ''
  try {
    await removeFromBookshelf(route.params.id)
    details.value.shelfEntry = null
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się usunąć książki z półki.'
  } finally {
    shelfLoading.value = false
  }
}

// po:
async function removeShelfEntry() {
  const ok = await executeShelf(async () => {
    await removeFromBookshelf(route.params.id)
    return true
  }, { fallback: 'Nie udało się usunąć książki z półki.' })
  if (ok) details.value.shelfEntry = null
}
```

**submitReview (linie 373-394):**
```js
// przed:
async function submitReview() {
  reviewLoading.value = true
  reviewError.value = ''
  reviewMessage.value = ''
  try {
    const created = await createBookReview(route.params.id, {
      rating: reviewForm.rating,
      content: reviewForm.content.trim(),
    })
    details.value.reviews = [created, ...(details.value.reviews || [])]
    randomReviews.value = pickRandomReviews(details.value.reviews, 6)
    reviewForm.content = ''
    reviewForm.rating = 5
    reviewMessage.value = 'Dodano recenzję.'
  } catch (err) {
    reviewError.value = err instanceof Error ? err.message : 'Nie udało się dodać recenzji.'
  } finally {
    reviewLoading.value = false
  }
}

// po:
async function submitReview() {
  const created = await executeReview(async () => {
    return await createBookReview(route.params.id, {
      rating: reviewForm.rating,
      content: reviewForm.content.trim(),
    })
  }, { fallback: 'Nie udało się dodać recenzji.' })
  if (created) {
    details.value.reviews = [created, ...(details.value.reviews || [])]
    randomReviews.value = pickRandomReviews(details.value.reviews, 6)
    reviewForm.content = ''
    reviewForm.rating = 5
    reviewMessage.value = 'Dodano recenzję.'
  }
}
```

**onMounted (linie 396-399):** pozostaje bez zmian — `loadDetails()` jest wywoływane.

Usuń nieużywane importy: `ref` jeśli nieużywany w innych miejscach (jest używany dla `details` i `randomReviews`), `reactive` dalej używany.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/BookDetailView.vue
git commit -m "refactor: useAsyncState in BookDetailView, remove refreshAuth (issue #32)"
```

---

### Task 6: Refactor ProfileView, BookshelfView, SettingsView

**Files:**
- Modify: `frontend/src/views/ProfileView.vue`
- Modify: `frontend/src/views/BookshelfView.vue`
- Modify: `frontend/src/views/SettingsView.vue`

- [ ] **Step 1: ProfileView**

W `frontend/src/views/ProfileView.vue`:

**Importy:**
```js
// usuń refreshAuth:
import { authState } from '../auth'
// dodaj:
import { useAsyncState } from '../composables/useAsyncState'
```

**Stan:**
```js
// przed:
const loading = ref(true)
const error = ref('')
const followError = ref('')
const followLoading = ref(false)

// po:
const { loading, error, execute } = useAsyncState()
const { loading: followLoading, error: followError, execute: executeFollow } = useAsyncState()
```

**loadProfile (linie 106-136):**
```js
// po:
async function loadProfile() {
  loading.value = true
  const result = await execute(async () => {
    return await fetchUserProfile(username.value)
  }, { fallback: 'Nie udało się pobrać profilu.' })
  if (result) {
    profile.value = result
    if (authState.authenticated) {
      const [followersData, followingData] = await Promise.all([
        fetchFollowers(username.value),
        fetchFollowing(username.value),
      ])
      followers.value = followersData
      following.value = followingData
    } else {
      followers.value = []
      following.value = []
    }
  } else {
    profile.value = null
  }
}
```

**toggleFollow (linie 138-155):**
```js
// po:
async function toggleFollow() {
  const ok = await executeFollow(async () => {
    if (isFollowing.value) {
      await unfollowUser(username.value)
    } else {
      await followUser(username.value)
    }
    return true
  }, { fallback: 'Nie udało się zapisać obserwowania.' })
  if (ok) {
    followers.value = await fetchFollowers(username.value)
  }
}
```

Usuń zbędny `ref` z importu jeśli tylko na loading/error.

- [ ] **Step 2: BookshelfView**

W `frontend/src/views/BookshelfView.vue`:

**Importy:**
```js
// usuń refreshAuth:
import { authState } from '../auth'
// dodaj:
import { useAsyncState } from '../composables/useAsyncState'
```

**Stan:**
```js
// przed:
const loading = ref(true)
const error = ref('')

// po:
const { loading, error, execute } = useAsyncState()
```

**loadBookshelf (linie 98-115):**
```js
// po:
async function loadBookshelf() {
  loading.value = true
  await execute(async () => {
    if (!authState.authenticated) {
      entries.value = []
      return
    }
    entries.value = await fetchBookshelf()
  }, { fallback: 'Nie udało się pobrać półki.' })
}
```

**changeStatus (linie 117-129):**
```js
// po:
async function changeStatus(entry, event) {
  const nextStatus = event.target.value
  const result = await execute(async () => {
    return await updateBookshelfStatus(entry.book.id, nextStatus)
  }, { fallback: 'Nie udało się zmienić statusu.' })
  if (result) {
    entries.value = entries.value.map((current) =>
      current.book.id === entry.book.id ? result : current,
    )
  } else {
    event.target.value = entry.status
  }
}
```

**removeEntry (linie 131-138):**
```js
// po:
async function removeEntry(entry) {
  const ok = await execute(async () => {
    await removeFromBookshelf(entry.book.id)
    return true
  }, { fallback: 'Nie udało się usunąć książki z półki.' })
  if (ok) {
    entries.value = entries.value.filter((current) => current.book.id !== entry.book.id)
  }
}
```

- [ ] **Step 3: SettingsView**

W `frontend/src/views/SettingsView.vue`:

**Importy:**
```js
// usuń refreshAuth:
import { authState, signOut } from '../auth'
// dodaj:
import { useAsyncState } from '../composables/useAsyncState'
```

**Stan:**
```js
// przed:
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')

// po:
const { loading, error, execute } = useAsyncState()
const { loading: saving, error: saveError, message, execute: executeSave } = useAsyncState()
```

**loadSettings (linie 108-126):**
```js
// po:
async function loadSettings() {
  loading.value = true
  await execute(async () => {
    if (!authState.authenticated) {
      settings.value = null
      return
    }
    settings.value = await fetchCurrentUserSettings()
    syncForm(settings.value)
  }, { fallback: 'Nie udało się pobrać ustawień.' })
}
```

**saveSettings (linie 128-143) — używa executeSave zamiast execute:**
```js
// po:
async function saveSettings() {
  const result = await executeSave(async () => {
    return await updateCurrentUserSettings({ ...form })
  }, { fallback: 'Nie udało się zapisać ustawień.' })
  if (result) {
    settings.value = result
    syncForm(settings.value)
    await refreshAuth()
    message.value = 'Zapisano zmiany profilu.'
  }
}
```

Uwaga: `refreshAuth()` jest nadal potrzebne w `saveSettings` (nie chodzi o inicjalizację, tylko o aktualizację po zmianie username).

**toggleVisibility (linie 145-163):**
```js
// po:
async function toggleVisibility() {
  if (!settings.value) return
  const result = await executeSave(async () => {
    return await updateCurrentUserVisibility(!settings.value.profilePublic)
  }, { fallback: 'Nie udało się zmienić widoczności.' })
  if (result) {
    settings.value = result
    syncForm(settings.value)
    message.value = 'Zmieniono widoczność profilu.'
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/ProfileView.vue frontend/src/views/BookshelfView.vue frontend/src/views/SettingsView.vue
git commit -m "refactor: useAsyncState in ProfileView, BookshelfView, SettingsView, remove refreshAuth (issue #32)"
```

---

### Task 7: Refactor AdminBooksView (useAsyncState + savingRowId)

**Files:**
- Modify: `frontend/src/views/admin/AdminBooksView.vue`

- [ ] **Step 1: Stan i importy**

Dodaj import:
```js
import { useAsyncState } from '../../composables/useAsyncState'
```

Usuń ręczne refy, zastąp:
```js
// przed:
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')

// po:
const savingRowId = ref(null)
const { loading, error, message, execute, clearFeedback } = useAsyncState()
```

Usuń ręczne `clearFeedback()` (jest wewnątrz `execute`):
```js
// usuń funkcję:
function clearFeedback() {
  error.value = ''
  message.value = ''
}
```

- [ ] **Step 2: loadBooks**

```js
// po:
async function loadBooks() {
  loading.value = true
  await execute(async () => {
    books.value = await fetchBooks('')
  }, { fallback: 'Nie udało się pobrać książek.' })
}
```

- [ ] **Step 3: createBook (globalna operacja)**

```js
// po:
async function createBook() {
  savingRowId.value = 'create'
  await execute(async () => {
    await createModeratorBook(normalizeBookPayload(createForm))
    createForm.title = ''
    createForm.author = ''
    createForm.year = 0
    createForm.pageCount = 0
    createForm.isbn = ''
    createForm.description = ''
    createForm.genres = ''
    createForm.tags = ''
    message.value = 'Dodano książkę.'
    await loadBooks()
  }, { fallback: 'Nie udało się dodać książki.' })
  savingRowId.value = null
}
```

- [ ] **Step 4: saveBook (per-row)**

```js
// po:
async function saveBook(bookId) {
  savingRowId.value = bookId
  await execute(async () => {
    await patchModeratorBook(bookId, normalizeBookPayload(editForm))
    editId.value = null
    message.value = 'Zapisano zmiany książki.'
    await loadBooks()
  }, { fallback: 'Nie udało się zapisać zmian książki.' })
  savingRowId.value = null
}
```

- [ ] **Step 5: removeBook (per-row)**

```js
// po:
async function removeBook(bookId) {
  if (!window.confirm('Czy na pewno usunąć książkę?')) return
  savingRowId.value = bookId
  await execute(async () => {
    await deleteModeratorBook(bookId)
    message.value = 'Usunięto książkę.'
    await loadBooks()
  }, { fallback: 'Nie udało się usunąć książki.' })
  savingRowId.value = null
}
```

- [ ] **Step 6: uploadContent (globalna)**

```js
// po:
async function uploadContent() {
  if (!contentBookId.value || !contentFile.value) return
  savingRowId.value = 'upload'
  const ok = await execute(async () => {
    await uploadModeratorBookContent(contentBookId.value, contentFile.value)
    return true
  }, { fallback: 'Nie udało się wgrać treści książki.' })
  if (ok) {
    contentFile.value = null
    message.value = 'Wgrano treść książki i uruchomiono analizę.'
  }
  savingRowId.value = null
}
```

- [ ] **Step 7: clearContent (globalna)**

```js
// po:
async function clearContent() {
  if (!contentBookId.value) return
  if (!window.confirm('Czy na pewno usunąć wszystkie rozdziały tej książki?')) return
  savingRowId.value = 'clear'
  const ok = await execute(async () => {
    await clearModeratorBookContent(contentBookId.value)
    return true
  }, { fallback: 'Nie udało się wyczyścić rozdziałów książki.' })
  if (ok) message.value = 'Wyczyszczono rozdziały książki.'
  savingRowId.value = null
}
```

- [ ] **Step 8: Aktualizuj template — przyciski**

Znajdź w template wszystkie `:disabled="saving"` i zastąp `:disabled="savingRowId !== null"`:

```html
<!-- przed: -->
<button class="btn btn-primary btn-sm" :disabled="saving" @click="createBook">Dodaj</button>

<!-- po: -->
<button class="btn btn-primary btn-sm" :disabled="savingRowId !== null" @click="createBook">Dodaj</button>
```

Dla przycisków per-row (save/edit/delete) również:
```html
<button class="btn btn-sm" :disabled="savingRowId !== null" @click="saveBook(book.id)">Zapisz</button>
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/views/admin/AdminBooksView.vue
git commit -m "refactor: useAsyncState + savingRowId in AdminBooksView (issue #32)"
```

---

### Task 8: Refactor AdminAuthorsView (useAsyncState + savingRowId)

**Files:**
- Modify: `frontend/src/views/admin/AdminAuthorsView.vue`

- [ ] **Step 1: Stan i importy (identyczny pattern jak AdminBooksView)**

Analogicznie do Task 7:

```js
import { useAsyncState } from '../../composables/useAsyncState'
```

```js
// przed:
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')

// po:
const savingRowId = ref(null)
const { loading, error, message, execute } = useAsyncState()
```

- [ ] **Step 2: loadAuthors, createAuthor, saveAuthor, removeAuthor**

Wszystkie 4 funkcje refaktorowane identycznie jak w AdminBooksView:
- `loadAuthors`: `execute` z fallbackiem 'Nie udało się pobrać autorów.'
- `createAuthor`: `savingRowId='create'`, `execute` z fallbackiem 'Nie udało się dodać autora.'
- `saveAuthor(authorId)`: `savingRowId=authorId`, `execute` z fallbackiem 'Nie udało się zapisać zmian autora.'
- `removeAuthor(authorId)`: `savingRowId=authorId`, `execute` z fallbackiem 'Nie udało się usunąć autora.'

- [ ] **Step 3: Aktualizuj template — :disabled="saving" → :disabled="savingRowId !== null"**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/admin/AdminAuthorsView.vue
git commit -m "refactor: useAsyncState + savingRowId in AdminAuthorsView (issue #32)"
```

---

### Task 9: Refactor AdminSeriesView (useAsyncState + savingRowId)

**Files:**
- Modify: `frontend/src/views/admin/AdminSeriesView.vue`

- [ ] **Step 1: Stan i importy (identyczny pattern)**

Analogicznie do Task 7 i 8:

```js
import { useAsyncState } from '../../composables/useAsyncState'
```

```js
// przed:
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')

// po:
const savingRowId = ref(null)
const { loading, error, message, execute } = useAsyncState()
```

- [ ] **Step 2: loadSeries, createSeries, saveSeries, removeSeries**

Wszystkie 4 funkcje refaktorowane identycznie:
- `loadSeries`: `execute` z fallbackiem 'Nie udało się pobrać serii.'
- `createSeries`: `savingRowId='create'`, `execute` z fallbackiem 'Nie udało się dodać serii.'
- `saveSeries(seriesId)`: `savingRowId=seriesId`, `execute` z fallbackiem 'Nie udało się zapisać zmian serii.'
- `removeSeries(seriesId)`: `savingRowId=seriesId`, `execute` z fallbackiem 'Nie udało się usunąć serii.'

- [ ] **Step 3: Aktualizuj template — :disabled="saving" → :disabled="savingRowId !== null"**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/admin/AdminSeriesView.vue
git commit -m "refactor: useAsyncState + savingRowId in AdminSeriesView (issue #32)"
```

---

### Task 10: Final build verification

- [ ] **Step 1: Zbuduj frontend**

```bash
cd frontend && npm run build
```

Oczekiwane: build przechodzi bez błędów, `dist/` wygenerowany.

- [ ] **Step 2: Sprawdź git status**

```bash
git status
```

Oczekiwane: czysty working tree.

- [ ] **Step 3: Sprawdź historię commitów**

```bash
git log --oneline main..HEAD
```

Oczekiwane: ~10 commitów na branchu `infra/issue-32-frontend-quality`.
