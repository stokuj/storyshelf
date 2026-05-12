<template>
  <section>
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h1 class="mb-1 text-3xl font-bold">Moja półka</h1>
        <p class="text-base-content/60">{{ filteredEntries.length }} książek</p>
      </div>
      <RouterLink to="/" class="btn btn-outline btn-sm">Przeglądaj katalog</RouterLink>
    </div>

    <div class="tabs tabs-box mb-6" role="tablist">
      <button
        v-for="option in filters"
        :key="option.value"
        class="tab"
        :class="{ 'tab-active': activeFilter === option.value }"
        type="button"
        @click="activeFilter = option.value"
      >
        {{ option.label }}
      </button>
    </div>

    <AlertMessage v-if="error" :message="error" class="mb-6" />
    <AlertMessage v-if="mutateError" type="warning" :message="mutateError" class="mb-6" />
    <LoadingSpinner v-else-if="loading" text="Ładowanie półki..." />
    <AlertMessage v-else-if="!authState.authenticated" type="warning" message="Zaloguj się, aby zobaczyć swoją półkę." class="mb-6" />

    <div v-else-if="filteredEntries.length" class="flex flex-col gap-3">
      <div v-for="entry in filteredEntries" :key="entry.id" class="card bg-base-100 shadow-sm transition-shadow hover:shadow">
        <div class="card-body flex flex-row items-center gap-4 p-4">
          <RouterLink :to="`/book/${entry.book.id}`" class="shrink-0">
            <div class="flex h-16 w-12 items-end rounded bg-gradient-to-br from-primary/20 to-secondary/20 p-1">
              <span class="line-clamp-2 text-xs font-semibold leading-tight">{{ entry.book.title }}</span>
            </div>
          </RouterLink>

          <div class="min-w-0 flex-1">
            <RouterLink :to="`/book/${entry.book.id}`" class="line-clamp-1 font-semibold hover:underline">
              {{ entry.book.title }}
            </RouterLink>
            <p class="text-sm text-base-content/60">{{ entry.book.author }}</p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <select class="select select-bordered select-sm" :value="entry.status" @change="changeStatus(entry, $event)">
              <option value="WANT_TO_READ">CHCĘ PRZECZYTAĆ</option>
              <option value="READING">CZYTAM</option>
              <option value="READ">PRZECZYTANE</option>
            </select>
          </div>

          <button type="button" class="btn btn-ghost btn-sm text-error" title="Usuń z półki" @click="removeEntry(entry)">
            ✕
          </button>
        </div>
      </div>
    </div>

    <div v-else class="py-20 text-center">
      <p class="mb-4 text-lg text-base-content/40">Twoja półka jest pusta.</p>
      <RouterLink to="/" class="btn btn-primary">Przeglądaj katalog</RouterLink>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchBookshelf, removeFromBookshelf, updateBookshelfStatus } from '../api'
import { authState } from '../auth'
import { useAsyncState } from '../composables/useAsyncState'
import AlertMessage from '../components/AlertMessage.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const activeFilter = ref('ALL')
const entries = ref([])
const { loading, error, execute } = useAsyncState()
const { loading: mutating, error: mutateError, execute: executeMutate } = useAsyncState()
loading.value = true

const filters = [
  { value: 'ALL', label: 'Wszystkie' },
  { value: 'WANT_TO_READ', label: 'Chcę przeczytać' },
  { value: 'READING', label: 'Czytam' },
  { value: 'READ', label: 'Przeczytane' },
]

const filteredEntries = computed(() => {
  if (!entries.value.length) {
    return []
  }

  if (activeFilter.value === 'ALL') {
    return entries.value
  }

  return entries.value.filter((entry) => entry.status === activeFilter.value)
})

async function loadBookshelf() {
  await execute(async () => {
    if (!authState.authenticated) {
      entries.value = []
      return
    }
    entries.value = await fetchBookshelf()
  }, { fallback: 'Nie udało się pobrać półki.' })
}

async function changeStatus(entry, event) {
  const nextStatus = event.target.value
  const result = await executeMutate(async () => {
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

async function removeEntry(entry) {
  const ok = await executeMutate(async () => {
    await removeFromBookshelf(entry.book.id)
    return true
  }, { fallback: 'Nie udało się usunąć książki z półki.' })
  if (ok) {
    entries.value = entries.value.filter((current) => current.book.id !== entry.book.id)
  }
}

onMounted(() => {
  loadBookshelf()
})
</script>
