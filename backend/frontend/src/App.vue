<template>
  <div class="min-h-screen bg-base-200">
    <nav class="navbar bg-base-100 px-4 shadow-sm">
      <div class="navbar-start">
        <RouterLink to="/" class="btn btn-ghost text-xl font-bold">SpringShelf</RouterLink>
      </div>

      <div class="navbar-center hidden md:flex">
        <RouterLink to="/" class="btn btn-ghost btn-sm">Katalog</RouterLink>
        <RouterLink v-if="authState.authenticated" to="/bookshelf" class="btn btn-ghost btn-sm">Moja półka</RouterLink>
        <RouterLink v-if="isModerator" to="/admin" class="btn btn-ghost btn-sm">Admin</RouterLink>
        <form class="ml-3" @submit.prevent="submitSearch">
          <label class="input input-bordered input-sm flex items-center gap-2">
            <input
              v-model="search"
              type="text"
              class="grow"
              placeholder="Szukaj książek"
            />
            <button class="btn btn-primary btn-xs" type="submit">Szukaj</button>
          </label>
        </form>
      </div>

      <div class="navbar-end gap-2">
        <template v-if="authState.authenticated">
          <RouterLink to="/bookshelf" class="btn btn-ghost btn-sm">Moja półka</RouterLink>
          <RouterLink v-if="isModerator" to="/admin" class="btn btn-ghost btn-sm">Admin</RouterLink>
          <RouterLink :to="`/profile/${authState.username}`" class="btn btn-ghost btn-sm">Profil</RouterLink>
          <RouterLink to="/settings" class="btn btn-ghost btn-sm">Ustawienia</RouterLink>
          <button class="btn btn-outline btn-sm" type="button" @click="handleLogout">Wyloguj</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn-ghost btn-sm">Zaloguj</RouterLink>
          <RouterLink to="/register" class="btn btn-primary btn-sm">Zarejestruj</RouterLink>
        </template>
      </div>
    </nav>

    <main class="container mx-auto max-w-7xl px-4 py-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { authState, refreshAuth, signOut } from './auth'

const route = useRoute()
const router = useRouter()
const search = ref(typeof route.query.q === 'string' ? route.query.q : '')
const isModerator = computed(() => authState.role === 'MODERATOR')

function submitSearch() {
  router.push({ path: '/', query: search.value.trim() ? { q: search.value.trim() } : {} })
}

async function handleLogout() {
  await signOut()
  router.push('/login')
}

onMounted(() => {
  refreshAuth()
})

watch(
  () => route.query.q,
  (value) => {
    search.value = typeof value === 'string' ? value : ''
  },
)
</script>
