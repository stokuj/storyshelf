<template>
  <section>
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>
    <div v-if="message" class="alert alert-success mb-4 text-sm">{{ message }}</div>

    <div class="card mb-5 bg-base-100 shadow-sm">
      <div class="card-body">
        <h2 class="card-title text-base">Dodaj autora</h2>
        <form class="grid gap-3 md:grid-cols-3" @submit.prevent="createAuthor">
          <input v-model="createForm.name" class="input input-bordered md:col-span-2" placeholder="Imię i nazwisko" required />
          <input v-model="createForm.birthDate" class="input input-bordered" type="date" />
          <textarea
            v-model="createForm.bio"
            class="textarea textarea-bordered md:col-span-3"
            rows="3"
            placeholder="Krótki opis autora"
          ></textarea>
          <div class="md:col-span-3">
            <button class="btn btn-primary btn-sm" type="submit" :disabled="savingRowId !== null">
              {{ savingRowId !== null ? 'Zapisywanie...' : 'Dodaj autora' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div class="card bg-base-100 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="p-6 text-sm text-base-content/60">Ładowanie autorów...</div>
        <div v-else-if="!authors.length" class="p-6 text-sm text-base-content/60">Brak autorów.</div>
        <div v-else class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Autor</th>
                <th>Data urodzenia</th>
                <th>Bio</th>
                <th class="w-44">Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="author in authors" :key="author.id">
                <template v-if="editId === author.id">
                  <td>
                    <input v-model="editForm.name" class="input input-bordered input-sm w-full" />
                  </td>
                  <td>
                    <input v-model="editForm.birthDate" class="input input-bordered input-sm w-full" type="date" />
                  </td>
                  <td>
                    <textarea v-model="editForm.bio" class="textarea textarea-bordered textarea-sm w-full" rows="2"></textarea>
                  </td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-primary btn-xs" type="button" :disabled="savingRowId !== null" @click="saveAuthor(author.id)">
                        Zapisz
                      </button>
                      <button class="btn btn-ghost btn-xs" type="button" :disabled="savingRowId !== null" @click="cancelEdit">
                        Anuluj
                      </button>
                    </div>
                  </td>
                </template>
                <template v-else>
                  <td class="font-medium">{{ author.name }}</td>
                  <td>{{ author.birthDate || '-' }}</td>
                  <td class="max-w-md truncate">{{ author.bio || '-' }}</td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-outline btn-xs" type="button" :disabled="savingRowId !== null" @click="startEdit(author)">
                        Edytuj
                      </button>
                      <button class="btn btn-error btn-xs" type="button" :disabled="savingRowId !== null" @click="removeAuthor(author.id)">
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
import {
  createModeratorAuthor,
  deleteModeratorAuthor,
  fetchAuthors,
  updateModeratorAuthor,
} from '../../api'
import { useAsyncState } from '../../composables/useAsyncState'

const authors = ref([])
const editId = ref(null)
const savingRowId = ref(null)
const { loading, error, message, execute } = useAsyncState()
loading.value = true

const createForm = reactive({
  name: '',
  bio: '',
  birthDate: '',
})

const editForm = reactive({
  name: '',
  bio: '',
  birthDate: '',
})

async function loadAuthors() {
  await execute(async () => {
    authors.value = await fetchAuthors()
  }, { fallback: 'Nie udało się pobrać autorów.' })
}

function normalizeAuthorPayload(form) {
  return {
    name: form.name.trim(),
    bio: form.bio.trim() || null,
    birthDate: form.birthDate || null,
  }
}

async function createAuthor() {
  savingRowId.value = 'create'
  const ok = await execute(async () => {
    await createModeratorAuthor(normalizeAuthorPayload(createForm))
    return true
  }, { fallback: 'Nie udało się dodać autora.' })
  savingRowId.value = null
  if (ok) {
    createForm.name = ''
    createForm.bio = ''
    createForm.birthDate = ''
    message.value = 'Dodano autora.'
    await loadAuthors()
  }
}

function startEdit(author) {
  editId.value = author.id
  editForm.name = author.name || ''
  editForm.bio = author.bio || ''
  editForm.birthDate = author.birthDate || ''
}

function cancelEdit() {
  editId.value = null
}

async function saveAuthor(authorId) {
  savingRowId.value = authorId
  const ok = await execute(async () => {
    await updateModeratorAuthor(authorId, normalizeAuthorPayload(editForm))
    return true
  }, { fallback: 'Nie udało się zapisać zmian autora.' })
  savingRowId.value = null
  if (ok) {
    editId.value = null
    message.value = 'Zapisano zmiany autora.'
    await loadAuthors()
  }
}

async function removeAuthor(authorId) {
  if (!window.confirm('Czy na pewno usunąć autora?')) return
  savingRowId.value = authorId
  const ok = await execute(async () => {
    await deleteModeratorAuthor(authorId)
    return true
  }, { fallback: 'Nie udało się usunąć autora.' })
  savingRowId.value = null
  if (ok) {
    message.value = 'Usunięto autora.'
    await loadAuthors()
  }
}

onMounted(() => {
  loadAuthors()
})
</script>
