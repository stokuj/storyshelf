<template>
  <section class="mx-auto max-w-6xl">

    <!-- Komunikaty globalne: blad i sukces po akcjach na polce -->
    <AlertMessage v-if="error" :message="error" class="mb-6" />

    <LoadingSpinner v-else-if="loading" text="Ładowanie książki..." />

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
          <div class="rounded-xl bg-base-100 shadow-sm p-3 flex flex-col gap-2">
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
            <button
              v-if="details.shelfEntry"
              type="button"
              class="btn btn-ghost btn-xs text-error"
              :disabled="shelfLoading"
              @click="removeShelfEntry"
            >
              Usuń z półki
            </button>
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
          <div v-if="details.book.avg_rating > 0" class="flex items-center gap-3 flex-wrap">
            <div class="rating rating-md">
              <input
                v-for="star in 5"
                :key="`right-star-${star}`"
                type="radio"
                class="mask mask-star-2 bg-orange-400"
                :checked="star <= Math.round(details.book.avg_rating)"
                disabled
              />
            </div>
            <span class="text-sm font-semibold text-orange-500">{{ details.book.avg_rating.toFixed(1) }}</span>
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

      <!-- Formularz recenzji -->
      <div v-if="authState.authenticated" class="card mt-8 bg-base-100 shadow-sm">
        <div class="card-body p-5">
          <h2 class="card-title text-base mb-3">Napisz recenzję</h2>
          <AlertMessage v-if="reviewError" :message="reviewError" class="mb-3" />
          <AlertMessage v-if="reviewMessage" type="success" :message="reviewMessage" class="mb-3" />
          <form class="space-y-3" @submit.prevent="submitReview">
            <div class="flex items-center gap-2">
              <span class="text-sm">Ocena:</span>
              <div class="rating rating-sm">
                <input
                  v-for="star in 5"
                  :key="`review-form-star-${star}`"
                  type="radio"
                  class="mask mask-star-2 bg-orange-400"
                  :value="star"
                  v-model="reviewForm.rating"
                />
              </div>
            </div>
            <textarea
              v-model="reviewForm.content"
              class="textarea textarea-bordered w-full"
              rows="3"
              placeholder="Twoja opinia o książce..."
            />
            <button
              type="submit"
              class="btn btn-primary btn-sm"
              :disabled="reviewLoading"
            >
              {{ reviewLoading ? 'Wysyłanie...' : 'Dodaj recenzję' }}
            </button>
          </form>
        </div>
      </div>

      <!-- Recenzje czytelników -->
      <div class="card mt-4 bg-base-100 shadow-sm">
        <div class="card-body p-5">
          <div class="flex items-center justify-between gap-2 mb-1">
            <h2 class="card-title text-base">Recenzje czytelników</h2>
            <div class="badge badge-neutral badge-outline">{{ sortedReviews.length }}</div>
          </div>

          <div v-if="sortedReviews.length" class="space-y-3 mt-2">
            <div
              v-for="review in sortedReviews"
              :key="review.id"
              class="border border-base-200 rounded-lg p-3"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-semibold">{{ review.username || 'Anonim' }}</span>
                <span v-if="review.createdAt" class="text-xs text-base-content/40">
                  {{ formatDate(review.createdAt) }}
                </span>
              </div>
              <div v-if="review.rating" class="mb-1">
                <div class="rating rating-xs">
                  <input
                    v-for="star in 5"
                    :key="`review-${review.id}-star-${star}`"
                    type="radio"
                    class="mask mask-star-2 bg-orange-400"
                    :checked="star <= review.rating"
                    disabled
                  />
                </div>
              </div>
              <p class="text-sm leading-relaxed text-base-content/80">{{ review.content || 'Brak treści.' }}</p>
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
                <span v-if="relation.relation_type" class="badge badge-sm badge-outline ml-1">{{ relation.relation_type }}</span>
              </div>
            </li>
          </ul>
          <div v-else class="text-sm text-base-content/40 italic pt-1">Brak danych o relacjach.</div>
        </div>
      </div>

    </template>

    <template v-else>
      <NotFoundState
        title="Książka nie istnieje"
        message="Nie znaleziono książki o podanym identyfikatorze."
      />
    </template>
  </section>
</template>

<script setup>
import { computed, reactive, onMounted, ref, watch } from 'vue'
import NotFoundState from '../components/NotFoundState.vue'
import AlertMessage from '../components/AlertMessage.vue'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import { useRoute } from 'vue-router'
import {
  addToBookshelf,
  createReview,
  fetchBookDetails,
  fetchReviews,
  removeFromBookshelf,
  updateBookshelfStatus,
} from '../api'
import { authState } from '../auth'
import { useAsyncState } from '../composables/useAsyncState'

const route = useRoute()

// Stan widoku i danych książki
const details = ref(null)
const { loading, error, execute } = useAsyncState()
loading.value = true

// Stan komunikatów/akcji użytkownika
const { loading: shelfLoading, execute: executeShelf } = useAsyncState()
const { loading: reviewLoading, error: reviewError, message: reviewMessage, execute: executeReview } = useAsyncState()
const sortedReviews = ref([])

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

function sortReviews(reviews, limit = 6) {
  if (!Array.isArray(reviews) || !reviews.length) {
    return []
  }

  return [...reviews]
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .slice(0, limit)
}

async function loadDetails() {
  const result = await execute(async () => {
    return await fetchBookDetails(route.params.id)
  }, { fallback: 'Nie udało się pobrać szczegółów książki.' })

  if (result) {
    details.value = result
    try {
      const reviews = await fetchReviews(route.params.id)
      sortedReviews.value = sortReviews(reviews || [], 6)
    } catch {
      sortedReviews.value = []
      reviewError.value = 'Nie udało się pobrać recenzji.'
    }
  } else {
    details.value = null
    sortedReviews.value = []
  }
}

async function addShelfEntry() {
  await executeShelf(async () => {
    details.value.shelfEntry = await addToBookshelf(route.params.id)
  }, { fallback: 'Nie udało się dodać książki do półki.' })
}

async function changeShelfStatusByValue(status) {
  await executeShelf(async () => {
    if (details.value?.shelfEntry) {
      details.value.shelfEntry = await updateBookshelfStatus(route.params.id, status)
    } else {
      details.value.shelfEntry = await addToBookshelf(route.params.id, status)
    }
  }, { fallback: 'Nie udało się zapisać statusu książki.' })
}

async function removeShelfEntry() {
  const result = await executeShelf(async () => {
    await removeFromBookshelf(route.params.id)
    return true
  }, { fallback: 'Nie udało się usunąć książki z półki.' })
  if (result) details.value.shelfEntry = null
}

async function submitReview() {
  const created = await executeReview(async () => {
    return await createReview({
      bookId: parseInt(route.params.id),
      rating: reviewForm.rating,
      content: reviewForm.content.trim(),
    })
  }, { fallback: 'Nie udało się dodać recenzji.' })

  if (created) {
    sortedReviews.value = sortReviews([created, ...sortedReviews.value], 6)
    reviewForm.content = ''
    reviewForm.rating = 5
    reviewMessage.value = 'Dodano recenzję.'
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
