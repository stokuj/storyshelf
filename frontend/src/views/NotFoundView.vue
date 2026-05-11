<template>
  <section class="py-20 text-center">
    <h1 class="mb-4 text-6xl font-bold text-base-content/30">404</h1>
    <p class="mb-6 text-lg text-base-content/60">Nie znaleziono strony.</p>
    <RouterLink to="/" class="btn btn-primary">Wróć do katalogu</RouterLink>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
