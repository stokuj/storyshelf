<template>
  <div class="min-h-screen bg-base-200">
    <nav class="navbar bg-base-100 px-4 shadow-sm">
      <div class="navbar-start">
        <div class="dropdown md:hidden">
          <button
            tabindex="0"
            role="button"
            class="btn btn-ghost btn-circle"
            aria-label="Menu"
            @click="menuOpen = !menuOpen"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <ul
            v-if="menuOpen"
            tabindex="0"
            class="menu menu-sm dropdown-content mt-3 z-[1] p-2 shadow bg-base-100 rounded-box w-52"
          >
            <li v-if="authState.authenticated">
              <RouterLink to="/bookshelf" @click="menuOpen = false">Moja półka</RouterLink>
            </li>
            <li v-if="authState.authenticated">
              <RouterLink :to="`/profile/${authState.username}`" @click="menuOpen = false">Profil</RouterLink>
            </li>
            <li v-if="!authState.authenticated">
              <RouterLink to="/login" @click="menuOpen = false">Zaloguj</RouterLink>
            </li>
            <li v-if="!authState.authenticated">
              <RouterLink to="/register" @click="menuOpen = false">Zarejestruj</RouterLink>
            </li>
            <li v-if="authState.authenticated">
              <button type="button" @click="handleLogoutMobile">Wyloguj</button>
            </li>
          </ul>
        </div>
        <RouterLink to="/" class="btn btn-ghost text-xl font-bold">StoryShelf</RouterLink>
      </div>

      <div class="navbar-end gap-2 hidden md:flex" v-if="authState.initialized">
        <template v-if="authState.authenticated">
          <RouterLink to="/bookshelf" class="btn btn-ghost btn-sm">Moja półka</RouterLink>
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
import { ref } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { authState, signOut } from './auth'

const router = useRouter()
const menuOpen = ref(false)

async function handleLogout() {
  await signOut()
  router.push('/login')
}

async function handleLogoutMobile() {
  menuOpen.value = false
  await handleLogout()
}
</script>
