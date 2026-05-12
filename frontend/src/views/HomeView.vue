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

    <AlertMessage v-if="error" :message="error" class="mb-6" />

    <div v-else-if="loading" class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
      <div v-for="n in 12" :key="`skeleton-${n}`" class="card bg-base-100 shadow">
        <div class="skeleton aspect-[2/3] rounded-t-box"></div>
        <div class="card-body p-3 space-y-2">
          <div class="skeleton h-4 w-3/4"></div>
          <div class="skeleton h-3 w-1/2"></div>
          <div class="skeleton h-6 w-full"></div>
        </div>
      </div>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        <BookCard v-for="book in books" :key="book.id" :book="book" />
      </div>

      <div v-if="!books.length" class="py-20 text-center">
        <p class="text-lg text-base-content/40">Brak książek w katalogu.</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { fetchBooks } from '../api'
import { useAsyncState } from '../composables/useAsyncState'
import AlertMessage from '../components/AlertMessage.vue'
import BookCard from '../components/BookCard.vue'

const route = useRoute()
const books = ref([])
const { loading, error, execute } = useAsyncState()
loading.value = true

async function loadBooks() {
  const query = typeof route.query.q === 'string' ? route.query.q : ''
  await execute(async () => {
    books.value = await fetchBooks(query)
  }, { fallback: 'Nie udało się pobrać książek.' })
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
