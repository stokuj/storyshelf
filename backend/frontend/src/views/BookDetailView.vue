<template>
  <section class="mx-auto max-w-6xl">
    
    <!-- Komunikaty globalne: blad i sukces po akcjach na polce -->
    <div v-if="error" class="alert alert-error mb-6 text-sm">{{ error }}</div>
    <div v-if="shelfMessage" class="alert alert-success mb-6 text-sm">{{ shelfMessage }}</div>
    <div v-else-if="loading" class="py-20 text-center text-base-content/60">Ładowanie szczegółów książki...</div>

    <template v-else-if="details">
      <!-- Okruszki nawigacji (powrot do katalogu) -->
      <div class="breadcrumbs mb-6 text-sm bg-base-100">
        <ul>
          <li><RouterLink to="/">Katalog</RouterLink></li>
          <li>{{ details.book.title }}</li>
        </ul>
      </div>

      // nie zmieniaj kodu powyżej tej lini

      <div class="grid grid-cols-1 gap-6 md:grid-cols-4 md:gap-8">
        <div class="md:col-span-1">
          <div class="flex h-72 w-48 items-end rounded-box bg-gradient-to-br from-primary/20 to-secondary/20 p-4">
            <div>
              <p class="text-sm font-bold">{{ details.book.title }}</p>
              <p class="mt-1 text-xs text-base-content/60">{{ details.book.author }}</p>
            </div>
          </div>
        </div>

        <div class="md:col-span-3">
          <h1 class="mb-1 text-3xl font-bold">{{ details.book.title }}</h1>
          <p class="mb-4 text-xl text-base-content/70">{{ details.book.author }}</p>

          <div v-if="details.book.description">
            <h2 class="mb-2 text-lg font-semibold">Opis</h2>
            <p class="leading-relaxed text-base-content/80">{{ details.book.description }}</p>
          </div>
        </div>
      </div>

      // nie zmieniaj kodu poniżej tej lini

    </template>
  </section>
</template>

<script setup>
import { reactive, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import {
  addToBookshelf,
  createBookReview,
  fetchBookDetails,
  removeFromBookshelf,
  updateBookshelfStatus,
} from '../api'
import { authState, refreshAuth } from '../auth'

const route = useRoute()
const details = ref(null)
const loading = ref(true)
const error = ref('')
const shelfLoading = ref(false)
const shelfMessage = ref('')
const reviewLoading = ref(false)
const reviewError = ref('')
const reviewMessage = ref('')
const reviewForm = reactive({
  rating: 5,
  content: '',
})

function formatDate(value) {
  if (!value) {
    return 'Brak daty'
  }

  return new Intl.DateTimeFormat('pl-PL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

async function loadDetails() {
  loading.value = true
  error.value = ''
  shelfMessage.value = ''

  try {
    await refreshAuth()
    details.value = await fetchBookDetails(route.params.id)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się pobrać szczegółów książki.'
  } finally {
    loading.value = false
  }
}

async function addShelfEntry() {
  shelfLoading.value = true
  error.value = ''
  shelfMessage.value = ''

  try {
    details.value.shelfEntry = await addToBookshelf(route.params.id)
    shelfMessage.value = 'Dodano książkę do półki.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się dodać książki do półki.'
  } finally {
    shelfLoading.value = false
  }
}

async function changeShelfStatus(event) {
  shelfLoading.value = true
  error.value = ''
  shelfMessage.value = ''
  const previousStatus = details.value?.shelfEntry?.status

  try {
    details.value.shelfEntry = await updateBookshelfStatus(route.params.id, event.target.value)
    shelfMessage.value = 'Zmieniono status książki.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zmienić statusu książki.'
    event.target.value = previousStatus
  } finally {
    shelfLoading.value = false
  }
}

async function removeShelfEntry() {
  shelfLoading.value = true
  error.value = ''
  shelfMessage.value = ''

  try {
    await removeFromBookshelf(route.params.id)
    details.value.shelfEntry = null
    shelfMessage.value = 'Usunięto książkę z półki.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się usunąć książki z półki.'
  } finally {
    shelfLoading.value = false
  }
}

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
    reviewForm.content = ''
    reviewForm.rating = 5
    reviewMessage.value = 'Dodano recenzję.'
  } catch (err) {
    reviewError.value = err instanceof Error ? err.message : 'Nie udało się dodać recenzji.'
  } finally {
    reviewLoading.value = false
  }
}

onMounted(() => {
  loadDetails()
})

watch(
  () => route.params.id,
  () => {
    loadDetails()
  },
)
</script>
