<template>
  <section>
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>
    <div v-if="message" class="alert alert-success mb-4 text-sm">{{ message }}</div>

    <div class="card mb-5 bg-base-100 shadow-sm">
      <div class="card-body">
        <h2 class="card-title text-base">Dodaj serię</h2>
        <form class="grid gap-3 md:grid-cols-3" @submit.prevent="createSeries">
          <input v-model="createForm.name" class="input input-bordered md:col-span-2" placeholder="Nazwa serii" required />
          <select v-model="createForm.status" class="select select-bordered">
            <option v-for="status in statusOptions" :key="`create-${status}`" :value="status">
              {{ status }}
            </option>
          </select>
          <textarea
            v-model="createForm.description"
            class="textarea textarea-bordered md:col-span-3"
            rows="3"
            placeholder="Opis serii"
          ></textarea>
          <div class="md:col-span-3">
            <button class="btn btn-primary btn-sm" type="submit" :disabled="savingRowId !== null">
              {{ savingRowId !== null ? 'Zapisywanie...' : 'Dodaj serię' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div class="card bg-base-100 shadow-sm">
      <div class="card-body p-0">
        <div v-if="loading" class="p-6 text-sm text-base-content/60">Ładowanie serii...</div>
        <div v-else-if="!seriesList.length" class="p-6 text-sm text-base-content/60">Brak serii.</div>
        <div v-else class="overflow-x-auto">
          <table class="table">
            <thead>
              <tr>
                <th>Seria</th>
                <th>Status</th>
                <th>Opis</th>
                <th class="w-44">Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="series in seriesList" :key="series.id">
                <template v-if="editId === series.id">
                  <td>
                    <input v-model="editForm.name" class="input input-bordered input-sm w-full" />
                  </td>
                  <td>
                    <select v-model="editForm.status" class="select select-bordered select-sm w-full">
                      <option v-for="status in statusOptions" :key="`edit-${series.id}-${status}`" :value="status">
                        {{ status }}
                      </option>
                    </select>
                  </td>
                  <td>
                    <textarea v-model="editForm.description" class="textarea textarea-bordered textarea-sm w-full" rows="2"></textarea>
                  </td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-primary btn-xs" type="button" :disabled="savingRowId !== null" @click="saveSeries(series.id)">
                        Zapisz
                      </button>
                      <button class="btn btn-ghost btn-xs" type="button" :disabled="savingRowId !== null" @click="cancelEdit">
                        Anuluj
                      </button>
                    </div>
                  </td>
                </template>
                <template v-else>
                  <td class="font-medium">{{ series.name }}</td>
                  <td>
                    <span class="badge badge-outline">{{ series.status }}</span>
                  </td>
                  <td class="max-w-md truncate">{{ series.description || '-' }}</td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-outline btn-xs" type="button" :disabled="savingRowId !== null" @click="startEdit(series)">
                        Edytuj
                      </button>
                      <button class="btn btn-error btn-xs" type="button" :disabled="savingRowId !== null" @click="removeSeries(series.id)">
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
import { useAsyncState } from '../../composables/useAsyncState'
import {
  createModeratorSeries,
  deleteModeratorSeries,
  fetchSeries,
  updateModeratorSeries,
} from '../../api'

const statusOptions = ['ONGOING', 'COMPLETED', 'CANCELLED', 'HIATUS']
const seriesList = ref([])
const savingRowId = ref(null)
const { loading, error, message, execute } = useAsyncState()
loading.value = true
const editId = ref(null)

const createForm = reactive({
  name: '',
  description: '',
  status: 'ONGOING',
})

const editForm = reactive({
  name: '',
  description: '',
  status: 'ONGOING',
})

function normalizeSeriesPayload(form) {
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    status: form.status,
  }
}

async function loadSeries() {
  await execute(async () => {
    seriesList.value = await fetchSeries()
  }, { fallback: 'Nie udało się pobrać serii.' })
}

async function createSeries() {
  savingRowId.value = 'create'
  const ok = await execute(async () => {
    await createModeratorSeries(normalizeSeriesPayload(createForm))
    return true
  }, { fallback: 'Nie udało się dodać serii.' })
  savingRowId.value = null
  if (ok) {
    createForm.name = ''
    createForm.description = ''
    createForm.status = 'ONGOING'
    message.value = 'Dodano serię.'
    await loadSeries()
  }
}

function startEdit(series) {
  editId.value = series.id
  editForm.name = series.name || ''
  editForm.description = series.description || ''
  editForm.status = series.status || 'ONGOING'
}

function cancelEdit() {
  editId.value = null
}

async function saveSeries(seriesId) {
  savingRowId.value = seriesId
  const ok = await execute(async () => {
    await updateModeratorSeries(seriesId, normalizeSeriesPayload(editForm))
    return true
  }, { fallback: 'Nie udało się zapisać zmian serii.' })
  savingRowId.value = null
  if (ok) {
    editId.value = null
    message.value = 'Zapisano zmiany serii.'
    await loadSeries()
  }
}

async function removeSeries(seriesId) {
  if (!window.confirm('Czy na pewno usunąć serię?')) return
  savingRowId.value = seriesId
  const ok = await execute(async () => {
    await deleteModeratorSeries(seriesId)
    return true
  }, { fallback: 'Nie udało się usunąć serii.' })
  savingRowId.value = null
  if (ok) {
    message.value = 'Usunięto serię.'
    await loadSeries()
  }
}

onMounted(() => {
  loadSeries()
})
</script>
