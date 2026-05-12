<template>
  <div class="card bg-base-100 shadow transition-shadow hover:shadow-md">
    <RouterLink :to="`/book/${book.id}`" class="block">
      <div class="flex aspect-[2/3] items-end rounded-t-box bg-gradient-to-br from-primary/20 to-secondary/20 p-3">
        <div>
          <p class="line-clamp-2 text-sm font-semibold">{{ book.title }}</p>
          <p class="mt-1 text-xs text-base-content/60">{{ firstAuthor }}</p>
        </div>
      </div>
    </RouterLink>

    <div class="card-body p-3">
      <div v-if="firstGenre" class="badge badge-sm badge-ghost">{{ firstGenre }}</div>
      <RouterLink class="btn btn-xs btn-outline btn-primary mt-1 w-full" :to="`/book/${book.id}`">Szczegóły</RouterLink>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps({
  book: {
    type: Object,
    required: true,
  },
})

const firstAuthor = computed(() => {
  const authors = props.book.authors
  if (authors?.length) {
    return typeof authors[0] === 'object' ? authors[0].name : authors[0]
  }
  return props.book.author || 'Autor nieznany'
})

const firstGenre = computed(() => {
  return props.book.genres?.[0] || null
})
</script>
