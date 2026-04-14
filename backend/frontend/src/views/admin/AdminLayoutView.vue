<template>
  <section>
    <div class="mb-6 rounded-box bg-base-100 p-5 shadow-sm">
      <p class="text-xs uppercase tracking-widest text-base-content/50">Panel moderatora</p>
      <h1 class="mt-1 text-2xl font-bold">Administracja katalogiem</h1>
      <p class="mt-2 text-sm text-base-content/70">
        Zarządzaj książkami, autorami i seriami z jednego miejsca.
      </p>
    </div>

    <div class="tabs tabs-boxed mb-5 w-fit bg-base-100 shadow-sm">
      <RouterLink to="/admin/books" class="tab" :class="route.path.startsWith('/admin/books') ? 'tab-active' : ''">
        Książki
      </RouterLink>
      <RouterLink to="/admin/authors" class="tab" :class="route.path.startsWith('/admin/authors') ? 'tab-active' : ''">
        Autorzy
      </RouterLink>
      <RouterLink to="/admin/series" class="tab" :class="route.path.startsWith('/admin/series') ? 'tab-active' : ''">
        Serie
      </RouterLink>
    </div>

    <RouterView />
  </section>
</template>

<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'

const route = useRoute()
</script>
