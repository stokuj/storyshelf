<template>
  <section>
    <div class="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="mb-1 text-3xl font-bold">
          <span v-if="route.query.q">Wyniki dla: {{ route.query.q }}</span>
          <span v-else>Katalog książek</span>
        </h1>
        <p class="text-base-content/60">{{ books.length }} książek</p>
      </div>
    </div>

    <div v-if="error" class="alert alert-error mb-6 text-sm">{{ error }}</div>
    <div v-else-if="loading" class="py-20 text-center text-base-content/60">Ładowanie katalogu...</div>

    <template v-else>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        <div
          v-for="book in books"
          :key="book.id"
          class="card bg-base-100 shadow transition-shadow hover:shadow-md"
        >
          <RouterLink :to="`/book/${book.id}`" class="block">
            <div class="flex aspect-[2/3] items-end rounded-t-box bg-gradient-to-br from-primary/20 to-secondary/20 p-3">
              <div>
                <p class="line-clamp-2 text-sm font-semibold">{{ book.title }}</p>
                <p class="mt-1 text-xs text-base-content/60">{{ book.author || 'Autor nieznany' }}</p>
              </div>
            </div>
          </RouterLink>

          <div class="card-body p-3">
            <div class="badge badge-sm badge-ghost">Vue</div>
            <RouterLink class="btn btn-xs btn-outline btn-primary mt-1 w-full" :to="`/book/${book.id}`">Szczegóły</RouterLink>
          </div>
        </div>
      </div>

      <div v-if="!books.length" class="py-20 text-center">
        <p class="text-lg text-base-content/40">Brak książek w katalogu.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { fetchBooks } from '../api'

const route = useRoute()
const books = ref([])
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

onMounted(() => {
  loadBooks()
})

watch(
  () => route.query.q,
  () => {
    loadBooks()
  },
)
</script>
