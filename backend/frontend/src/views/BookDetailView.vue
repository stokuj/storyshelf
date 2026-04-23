<template>
  <section class="mx-auto max-w-6xl">

    <!-- Komunikaty globalne: blad i sukces po akcjach na polce -->
    <div v-if="error" class="alert alert-error mb-6 text-sm">{{ error }}</div>
    <div v-else-if="loading" class="py-20 text-center text-base-content/60">Ładowanie szczegółów książki...</div>

    <template v-else-if="details">

      <!-- nie zmieniaj kodu powyżej tej linii -->

      <!-- Układ 1:3 (lewa: okładka, prawa: podstawowe informacje o książce) -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-4 md:gap-8">

        <!-- Lewa kolumna (1/4): okładka + ocena + półka -->
        <div class="md:col-span-1 flex flex-col gap-3">

          <!-- Okładka -->
          <div class="relative mx-auto w-3/4 aspect-[2/3] rounded-xl overflow-hidden shadow-xl bg-gradient-to-br from-primary/30 via-secondary/20 to-accent/20 flex flex-col items-center justify-center gap-3 group">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 text-base-content/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.966 8.966 0 00-6 2.292m0-14.25v14.25" />
            </svg>
            <span class="text-xs text-base-content/30 tracking-widest uppercase">Okładka</span>
            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>

          <!-- Status czytania -->
          <div class="rounded-xl bg-base-100 shadow-sm p-3 flex flex-col gap-1">
            <select
              class="select select-bordered select-sm w-full"
              :value="details.shelfEntry?.status || 'WANT_TO_READ'"
              :disabled="shelfLoading"
              @change="changeShelfStatusByValue($event.target.value)"
            >
              <option value="WANT_TO_READ">Chcę przeczytać</option>
              <option value="READING">Czytam</option>
              <option value="READ">Przeczytana</option>
            </select>
          </div>

        </div>

        <!-- Prawa kolumna (3/4): tytuł, autor, opis -->
        <div class="md:col-span-3 flex flex-col gap-4">

          <!-- Seria -->
          <div v-if="seriesLabel">
            <span class="badge badge-outline badge-md">📖 Seria: {{ seriesLabel }}</span>
          </div>

          <!-- Tytuł i autor -->
          <div>
            <h1 class="text-4xl font-extrabold leading-tight tracking-tight">{{ details.book.title }}</h1>
            <p class="mt-1 text-xl text-base-content/60 font-medium">{{ details.book.author }}</p>
          </div>

          <!-- Ocena szczegółowa -->
          <div v-if="details.book.rating > 0" class="flex items-center gap-3 flex-wrap">
            <div class="rating rating-md">
              <input
                v-for="star in 5"
                :key="`right-star-${star}`"
                type="radio"
                class="mask mask-star-2 bg-orange-400"
                :checked="star <= Math.round(details.book.rating)"
                disabled
              />
            </div>
            <span class="text-sm font-semibold text-orange-500">{{ details.book.rating.toFixed(1) }}</span>
            <span class="text-sm text-base-content/40">• {{ details.book.ratingsCount }} ocen</span>
          </div>

          <!-- Gatunki i tagi -->
          <div v-if="details.book.genres?.length || details.book.tags?.length" class="flex flex-col gap-2">
            <div v-if="details.book.genres?.length" class="flex flex-wrap gap-2">
              <span
                v-for="genre in details.book.genres"
                :key="`genre-${genre}`"
                class="badge badge-outline"
              >
                {{ genre }}
              </span>
            </div>
            <div v-if="details.book.tags?.length" class="flex flex-wrap gap-2">
              <span
                v-for="tag in details.book.tags"
                :key="`tag-${tag}`"
                class="badge badge-ghost"
              >
                #{{ tag }}
              </span>
            </div>
          </div>

          <div class="divider my-0" />

          <!-- Opis -->
          <div v-if="details.book.description" class="flex flex-col gap-2">
            <h2 class="text-xs font-semibold uppercase tracking-widest text-base-content/50">Opis</h2>
            <p class="leading-relaxed text-base-content/75 text-[15px]">{{ details.book.description }}</p>
          </div>
          <div v-else class="text-sm text-base-content/40 italic">Brak opisu.</div>

        </div>
      </div>

      <!-- nie zmieniaj kodu poniżej tej linii -->

      <!-- Recenzje czytelników (losowe, układ lewo/prawo) -->
      <div class="card mt-8 bg-base-100 shadow-sm">
        <div class="card-body p-5">
          <div class="flex items-center justify-between gap-2 mb-1">
            <h2 class="card-title text-base">💬 Recenzje czytelników</h2>
            <div class="badge badge-neutral badge-outline">{{ randomReviews.length }}</div>
          </div>

          <div v-if="randomReviews.length" class="space-y-1 mt-2">
            <div
              v-for="(review, index) in randomReviews"
              :key="review.id || `random-review-${index}`"
              class="chat"
              :class="index % 2 === 0 ? 'chat-start' : 'chat-end'"
            >
              <div class="chat-header text-xs text-base-content/50 mb-0.5">
                {{ review.username || 'Anonim' }}
              </div>
              <div class="chat-bubble chat-bubble-primary max-w-2xl">
                <div class="mb-1" v-if="review.rating">
                  <div class="rating rating-xs">
                    <input
                      v-for="star in 5"
                      :key="`random-review-${review.id || index}-star-${star}`"
                      type="radio"
                      class="mask mask-star-2 bg-orange-400"
                      :checked="star <= review.rating"
                      disabled
                    />
                  </div>
                </div>
                <p class="text-sm leading-relaxed">{{ review.content || 'Brak treści.' }}</p>
              </div>
              <div class="chat-footer text-xs text-base-content/40 mt-0.5" v-if="review.createdAt">
                {{ formatDate(review.createdAt) }}
              </div>
            </div>
          </div>

          <div v-else class="text-sm text-base-content/40 italic pt-1">Brak recenzji.</div>
        </div>
      </div>

      <!-- Postacie (poniżej sekcji okładka + opis) -->
      <div class="card mt-4 bg-base-100 shadow-sm">
        <div class="card-body p-5">
          <div class="flex items-center justify-between gap-2 mb-1">
            <h2 class="card-title text-base">🧑‍🤝‍🧑 Postacie</h2>
            <div class="badge badge-neutral badge-outline">{{ details.characters?.length || 0 }}</div>
          </div>
          <div v-if="details.characters?.length" class="overflow-x-auto mt-2">
            <table class="table table-sm">
              <thead>
                <tr class="text-base-content/50 text-xs uppercase tracking-wide">
                  <th>Imię</th>
                  <th class="text-right">Wzmianki</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="character in details.characters"
                  :key="character.id"
                  class="hover:bg-base-200/50 transition-colors"
                >
                  <td class="font-semibold">{{ character.name }}</td>
                  <td class="text-right">
                    <span class="badge badge-sm badge-ghost">{{ character.mentionCount }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="text-sm text-base-content/40 italic pt-1">Brak danych o postaciach.</div>
        </div>
      </div>

      <!-- Relacje (poniżej sekcji postaci) -->
      <div class="card mt-4 bg-base-100 shadow-sm">
        <div class="card-body p-5">
          <div class="flex items-center justify-between gap-2 mb-1">
            <h2 class="card-title text-base">🔗 Relacje</h2>
            <div class="badge badge-neutral badge-outline">{{ details.relations?.length || 0 }}</div>
          </div>
          <ul v-if="details.relations?.length" class="divide-y divide-base-200 mt-2">
            <li
              v-for="relation in details.relations"
              :key="relation.id"
              class="py-3 flex flex-col gap-1 first:pt-0 last:pb-0"
            >
              <div class="flex items-center gap-2 flex-wrap text-sm">
                <span class="font-semibold">{{ relation.sourceCharacterName }}</span>
                <span class="text-base-content/30">↔</span>
                <span class="font-semibold">{{ relation.targetCharacterName }}</span>
                <span v-if="relation.relation" class="badge badge-sm badge-outline ml-1">{{ relation.relation }}</span>
              </div>
              <div v-if="relation.evidence" class="text-xs text-base-content/50 italic pl-0.5">
                {{ relation.evidence }}
              </div>
            </li>
          </ul>
          <div v-else class="text-sm text-base-content/40 italic pt-1">Brak danych o relacjach.</div>
        </div>
      </div>

    </template>
  </section>
</template>

<script setup>
import { computed, reactive, onMounted, ref, watch } from 'vue'
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

// Stan widoku i danych książki
const details = ref(null)
const loading = ref(true)
const error = ref('')

// Stan komunikatów/akcji użytkownika
const shelfLoading = ref(false)
const reviewLoading = ref(false)
const reviewError = ref('')
const reviewMessage = ref('')
const randomReviews = ref([])

// Formularz dodawania recenzji
const reviewForm = reactive({
  rating: 5,
  content: '',
})

const seriesLabel = computed(() => {
  const book = details.value?.book
  return book?.series?.name || book?.seriesName || book?.seriesTitle || ''
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

function pickRandomReviews(reviews, limit = 6) {
  if (!Array.isArray(reviews) || !reviews.length) {
    return []
  }

  const shuffled = [...reviews]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    const temp = shuffled[i]
    shuffled[i] = shuffled[j]
    shuffled[j] = temp
  }

  return shuffled.slice(0, limit)
}

async function loadDetails() {
  // Główne pobieranie danych książki po ID z URL
  loading.value = true
  error.value = ''

  try {
    await refreshAuth()
    details.value = await fetchBookDetails(route.params.id)
    randomReviews.value = pickRandomReviews(details.value?.reviews || [], 6)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się pobrać szczegółów książki.'
    randomReviews.value = []
  } finally {
    loading.value = false
  }
}

async function addShelfEntry() {
  // Dodanie książki do półki użytkownika
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

async function changeShelfStatus(event) {
  // Zmiana statusu książki na półce (np. WANT_TO_READ -> READING)
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

async function removeShelfEntry() {
  // Usunięcie książki z półki użytkownika
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

async function submitReview() {
  // Dodanie recenzji i dopięcie jej na początku listy
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

onMounted(() => {
  // Pierwsze załadowanie widoku
  loadDetails()
})

watch(
  () => route.params.id,
  () => {
    // Przeładowanie danych po zmianie ID książki w URL
    loadDetails()
  },
)
</script>
