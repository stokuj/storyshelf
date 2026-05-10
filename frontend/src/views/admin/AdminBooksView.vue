<template>
  <section>
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>
    <div v-if="message" class="alert alert-success mb-4 text-sm">{{ message }}</div>

    <div class="card mb-5 bg-base-100 shadow-sm">
      <div class="card-body">
        <h2 class="card-title text-base">Dodaj książkę</h2>
        <form class="grid gap-3 md:grid-cols-2" @submit.prevent="createBook">
          <input v-model="createForm.title" class="input input-bordered" placeholder="Tytuł" required />
          <input v-model="createForm.author" class="input input-bordered" placeholder="Autor" required />
          <input v-model.number="createForm.year" class="input input-bordered" type="number" min="0" placeholder="Rok" />
          <input
            v-model.number="createForm.pageCount"
            class="input input-bordered"
            type="number"
            min="0"
            placeholder="Liczba stron"
          />
          <input v-model="createForm.isbn" class="input input-bordered md:col-span-2" placeholder="ISBN" />
          <textarea
            v-model="createForm.description"
            class="textarea textarea-bordered md:col-span-2"
            rows="3"
            placeholder="Opis"
          ></textarea>
          <input v-model="createForm.genres" class="input input-bordered md:col-span-2" placeholder="Gatunki (oddziel przecinkami)" />
          <input v-model="createForm.tags" class="input input-bordered md:col-span-2" placeholder="Tagi (oddziel przecinkami)" />
          <div class="md:col-span-2">
            <button class="btn btn-primary btn-sm" type="submit" :disabled="savingRowId !== null">
              {{ savingRowId !== null ? 'Zapisywanie...' : 'Dodaj książkę' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div class="card mb-5 bg-base-100 shadow-sm">
      <div class="card-body">
        <h2 class="card-title text-base">Treść i rozdziały</h2>
        <div class="grid gap-3 md:grid-cols-[1fr_auto]">
          <select v-model="contentBookId" class="select select-bordered w-full">
            <option value="">Wybierz książkę</option>
            <option v-for="book in books" :key="`content-${book.id}`" :value="String(book.id)">
              {{ book.title }} - {{ book.author }}
            </option>
          </select>
          <RouterLink
            v-if="contentBookId"
            :to="`/book/${contentBookId}`"
            class="btn btn-outline btn-sm"
          >
            Podgląd książki
          </RouterLink>
        </div>
        <input
          type="file"
          class="file-input file-input-bordered mt-3 w-full"
          accept=".txt"
          @change="onContentFileChange"
        />
        <div class="mt-3 flex flex-wrap gap-2">
          <button class="btn btn-primary btn-sm" type="button" :disabled="savingRowId !== null || !contentBookId || !contentFile" @click="uploadContent">
            {{ savingRowId !== null ? 'Wysyłanie...' : 'Wyślij plik rozdziałów' }}
          </button>
          <button class="btn btn-error btn-sm" type="button" :disabled="savingRowId !== null || !contentBookId" @click="clearContent">
            {{ savingRowId !== null ? 'Czyszczenie...' : 'Wyczyść rozdziały książki' }}
          </button>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="p-6 text-sm text-base-content/60">Ładowanie książek...</div>
        <div v-else-if="!books.length" class="p-6 text-sm text-base-content/60">Brak książek.</div>
        <div v-else class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Książka</th>
                <th>Rok</th>
                <th>Stron</th>
                <th>ISBN</th>
                <th class="w-52">Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="book in books" :key="book.id">
                <template v-if="editId === book.id">
                  <td>
                    <div class="grid gap-2">
                      <input v-model="editForm.title" class="input input-bordered input-sm" placeholder="Tytuł" />
                      <input v-model="editForm.author" class="input input-bordered input-sm" placeholder="Autor" />
                    </div>
                  </td>
                  <td>
                    <input v-model.number="editForm.year" class="input input-bordered input-sm w-24" type="number" min="0" />
                  </td>
                  <td>
                    <input v-model.number="editForm.pageCount" class="input input-bordered input-sm w-24" type="number" min="0" />
                  </td>
                  <td>
                    <input v-model="editForm.isbn" class="input input-bordered input-sm w-36" placeholder="ISBN" />
                  </td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-primary btn-xs" type="button" :disabled="savingRowId !== null" @click="saveBook(book.id)">
                        Zapisz
                      </button>
                      <button class="btn btn-ghost btn-xs" type="button" :disabled="savingRowId !== null" @click="cancelEdit">
                        Anuluj
                      </button>
                    </div>
                  </td>
                </template>
                <template v-else>
                  <td>
                    <p class="font-medium">{{ book.title }}</p>
                    <p class="text-xs text-base-content/60">{{ book.author }}</p>
                  </td>
                  <td>{{ book.year || '-' }}</td>
                  <td>{{ book.pageCount || '-' }}</td>
                  <td>{{ book.isbn || '-' }}</td>
                  <td>
                    <div class="flex flex-wrap gap-2">
                      <RouterLink :to="`/book/${book.id}`" class="btn btn-ghost btn-xs">Podgląd</RouterLink>
                      <button class="btn btn-outline btn-xs" type="button" :disabled="savingRowId !== null" @click="startEdit(book)">
                        Edytuj
                      </button>
                      <button class="btn btn-error btn-xs" type="button" :disabled="savingRowId !== null" @click="removeBook(book.id)">
                        Usuń
                      </button>
                    </div>
                  </td>
                </template>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import {
  clearModeratorBookContent,
  createModeratorBook,
  deleteModeratorBook,
  fetchBooks,
  patchModeratorBook,
  uploadModeratorBookContent,
} from '../../api'
import { useAsyncState } from '../../composables/useAsyncState'

const books = ref([])
const savingRowId = ref(null)
const { loading, error, message, execute } = useAsyncState()
loading.value = true
const editId = ref(null)
const contentBookId = ref('')
const contentFile = ref(null)

const createForm = reactive({
  title: '',
  author: '',
  year: 0,
  pageCount: 0,
  isbn: '',
  description: '',
  genres: '',
  tags: '',
})

const editForm = reactive({
  title: '',
  author: '',
  year: 0,
  pageCount: 0,
  isbn: '',
  description: '',
  genres: '',
  tags: '',
})

function splitCsv(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function normalizeBookPayload(form) {
  return {
    title: form.title.trim(),
    author: form.author.trim(),
    year: form.year || 0,
    pageCount: form.pageCount || 0,
    isbn: form.isbn.trim() || null,
    description: form.description.trim() || null,
    genres: splitCsv(form.genres),
    tags: splitCsv(form.tags),
  }
}

async function loadBooks() {
  await execute(async () => {
    books.value = await fetchBooks('')
  }, { fallback: 'Nie udało się pobrać książek.' })
}

async function createBook() {
  savingRowId.value = 'create'
  const ok = await execute(async () => {
    await createModeratorBook(normalizeBookPayload(createForm))
    return true
  }, { fallback: 'Nie udało się dodać książki.' })
  savingRowId.value = null
  if (ok) {
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
  }
}

function startEdit(book) {
  editId.value = book.id
  editForm.title = book.title || ''
  editForm.author = book.author || ''
  editForm.year = book.year || 0
  editForm.pageCount = book.pageCount || 0
  editForm.isbn = book.isbn || ''
  editForm.description = book.description || ''
  editForm.genres = (book.genres || []).join(', ')
  editForm.tags = (book.tags || []).join(', ')
}

function cancelEdit() {
  editId.value = null
}

async function saveBook(bookId) {
  savingRowId.value = bookId
  const ok = await execute(async () => {
    await patchModeratorBook(bookId, normalizeBookPayload(editForm))
    return true
  }, { fallback: 'Nie udało się zapisać zmian książki.' })
  savingRowId.value = null
  if (ok) {
    editId.value = null
    message.value = 'Zapisano zmiany książki.'
    await loadBooks()
  }
}

async function removeBook(bookId) {
  if (!window.confirm('Czy na pewno usunąć książkę?')) return
  savingRowId.value = bookId
  const ok = await execute(async () => {
    await deleteModeratorBook(bookId)
    return true
  }, { fallback: 'Nie udało się usunąć książki.' })
  savingRowId.value = null
  if (ok) {
    message.value = 'Usunięto książkę.'
    await loadBooks()
  }
}

function onContentFileChange(event) {
  contentFile.value = event.target.files?.[0] || null
}

async function uploadContent() {
  if (!contentBookId.value || !contentFile.value) return
  savingRowId.value = 'upload'
  const ok = await execute(async () => {
    await uploadModeratorBookContent(contentBookId.value, contentFile.value)
    return true
  }, { fallback: 'Nie udało się wgrać treści książki.' })
  savingRowId.value = null
  if (ok) {
    contentFile.value = null
    message.value = 'Wgrano treść książki i uruchomiono analizę.'
  }
}

async function clearContent() {
  if (!contentBookId.value) return
  if (!window.confirm('Czy na pewno usunąć wszystkie rozdziały tej książki?')) return
  savingRowId.value = 'clear'
  const ok = await execute(async () => {
    await clearModeratorBookContent(contentBookId.value)
    return true
  }, { fallback: 'Nie udało się wyczyścić rozdziałów książki.' })
  savingRowId.value = null
  if (ok) {
    message.value = 'Wyczyszczono rozdziały książki.'
  }
}

onMounted(() => {
  loadBooks()
})
</script>
