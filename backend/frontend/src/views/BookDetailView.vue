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
      <div class="flex flex-col gap-8 md:flex-row bg-base-100">
        <!-- Lewa kolumna: uproszczona okladka -->
        <div class="shrink-0">
          <div class="flex h-72 w-48 items-end rounded-box bg-gradient-to-br from-primary/20 to-secondary/20 p-4">
            <div>
              <p class="text-sm font-bold">{{ details.book.title }}</p>
              <p class="mt-1 text-xs text-base-content/60">{{ details.book.author }}</p>
            </div>
          </div>
        </div>

        <div class="flex-1">
        <!-- Prawa kolumna: tytul, autor i metadane -->
        <h1 class="mb-1 text-3xl font-bold">{{ details.book.title }}</h1>
        <p class="mb-4 text-xl text-base-content/70">{{ details.book.author }}</p>

        <div class="mb-5 flex flex-wrap gap-3 text-sm text-base-content/60">
          <span v-if="details.book.year">{{ details.book.year }}</span>
          <span v-if="details.book.pageCount">{{ details.book.pageCount }} stron</span>
          <span v-if="details.book.isbn">ISBN: {{ details.book.isbn }}</span>
        </div>


        <!-- Gatunki -->
        <div v-if="details.book.genres?.length" class="mb-5 flex flex-wrap gap-2">
          <span v-for="genre in details.book.genres" :key="genre" class="badge badge-outline">
            {{ genre }}
          </span>
        </div>

        <!-- Srednia ocena ksiazki -->
        <div v-if="details.book.rating > 0" class="mb-5 flex items-center gap-2">
          <div class="rating rating-sm">
            <input
              v-for="star in 5"
              :key="star"
              type="radio"
              class="mask mask-star-2 bg-orange-400"
              :checked="star <= Math.round(details.book.rating)"
              disabled
            />
          </div>
          <span class="text-sm text-base-content/60">
            {{ details.book.rating.toFixed(1) }} ({{ details.book.ratingsCount }} ocen)
          </span>
        </div>




        <!-- Opis i tagi ksiazki -->
        <div v-if="details.book.description">
          <h2 class="mb-2 text-lg font-semibold">Opis</h2>
          <p class="leading-relaxed text-base-content/80">{{ details.book.description }}</p>
        </div>

        <div v-if="details.book.tags?.length" class="mt-4 flex flex-wrap gap-2">
          <span v-for="tag in details.book.tags" :key="tag" class="badge badge-ghost text-xs">{{ tag }}</span>
        </div>


        <!-- Tabela postaci wykrytych w ksiazce -->
        <div class="card mt-6 bg-base-100 p-4 shadow-sm">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="text-sm font-semibold">Postacie</h2>
            <div class="badge badge-outline">{{ details.characters.length }}</div>
          </div>
          <div v-if="details.characters?.length" class="overflow-x-auto">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Imię</th>
                  <th>Wzmianki</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="character in details.characters" :key="character.id">
                  <td class="font-medium">{{ character.name }}</td>
                  <td>{{ character.mentionCount }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="text-sm text-base-content/60">Brak danych o postaciach.</div>
        </div>

        <!-- Relacje miedzy postaciami -->
        <div class="card mt-4 bg-base-100 p-4 shadow-sm">
          <div class="mb-3 flex items-center justify-between gap-2">
            <h2 class="text-sm font-semibold">Relacje</h2>
            <div class="badge badge-outline">{{ details.relations.length }}</div>
          </div>
          <ul v-if="details.relations?.length" class="space-y-2">
            <li v-for="relation in details.relations" :key="relation.id" class="text-sm">
              <span class="font-medium">{{ relation.sourceCharacterName }}</span>
              <span class="text-base-content/60"> - </span>
              <span class="font-medium">{{ relation.targetCharacterName }}</span>
              <span v-if="relation.relation" class="text-base-content/60"> • </span>
              <span v-if="relation.relation">{{ relation.relation }}</span>
              <div v-if="relation.evidence" class="mt-1 text-xs text-base-content/60">
                {{ relation.evidence }}
              </div>
            </li>
          </ul>
          <div v-else class="text-sm text-base-content/60">Brak danych o relacjach.</div>
        </div>
        <!-- Relacje miedzy postaciami -->
        </div>
      </div>
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
