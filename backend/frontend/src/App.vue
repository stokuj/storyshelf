<template>
  <div class="min-h-screen bg-base-200">
    <nav class="navbar bg-base-100 px-4 shadow-sm">
      <div class="navbar-start">
        <RouterLink to="/" class="btn btn-ghost text-xl font-bold">SpringShelf</RouterLink>
      </div>

      <div class="navbar-end gap-2">
        <template v-if="authState.authenticated">
          <RouterLink :to="`/profile/${authState.username}`" class="btn btn-ghost btn-sm">Profil</RouterLink>
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
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { authState, refreshAuth, signOut } from './auth'

const router = useRouter()

async function handleLogout() {
  await signOut()
  router.push('/login')
}

onMounted(() => {
  refreshAuth()
})
</script>
