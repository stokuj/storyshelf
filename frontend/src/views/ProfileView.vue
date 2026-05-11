<template>
  <section class="max-w-lg mx-auto">
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>
    <div v-else-if="loading" class="py-20 text-center text-base-content/60">Ładowanie profilu...</div>

    <div v-else-if="profile" class="card bg-base-100 shadow">
      <div class="card-body">
        <div class="flex items-center gap-4">
          <div class="avatar">
            <div class="w-16 rounded-full bg-base-200 text-base-content">
              <img v-if="profile.avatarUrl" :src="profile.avatarUrl" alt="avatar" />
              <span v-else class="text-lg font-semibold">{{ initial }}</span>
            </div>
          </div>
          <div>
            <h1 class="text-xl font-bold">{{ profile.username }}</h1>
            <p class="text-sm text-base-content/60">Członek od {{ formatDate(profile.memberSince) }}</p>
          </div>
        </div>

        <div class="divider"></div>

        <div class="stats stats-vertical mb-4 border border-base-200 sm:stats-horizontal">
          <div class="stat py-3">
            <div class="stat-title">Followers</div>
            <div class="stat-value text-2xl">{{ followers.length }}</div>
          </div>
          <div class="stat py-3">
            <div class="stat-title">Following</div>
            <div class="stat-value text-2xl">{{ following.length }}</div>
          </div>
        </div>

        <div>
          <h2 class="mb-2 text-base font-semibold">O mnie</h2>
          <p class="text-sm text-base-content/80">{{ profile.bio || 'Brak opisu.' }}</p>
        </div>

        <div class="mt-4 flex flex-wrap gap-2">
          <RouterLink v-if="isOwner" to="/settings" class="btn btn-outline btn-sm">Edytuj profil</RouterLink>
          <button
            v-else-if="authState.authenticated"
            type="button"
            class="btn btn-primary btn-sm"
            :class="{ 'btn-outline': isFollowing }"
            :disabled="followLoading"
            @click="toggleFollow"
          >
            {{ followLoading ? 'Zapisywanie...' : isFollowing ? 'Przestań obserwować' : 'Obserwuj' }}
          </button>
          <RouterLink v-else to="/login" class="btn btn-primary btn-sm">Zaloguj się, aby obserwować</RouterLink>
        </div>

        <div v-if="authState.authenticated && followError" class="alert alert-warning mt-4 text-sm">
          {{ followError }}
        </div>
      </div>
    </div>

    <template v-else>
      <NotFoundState
        title="Użytkownik nie znaleziony"
        message="Profil o podanej nazwie nie istnieje."
      />
    </template>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import NotFoundState from '../components/NotFoundState.vue'
import { fetchFollowers, fetchFollowing, fetchUserProfile, followUser, unfollowUser } from '../api'
import { authState } from '../auth'
import { useAsyncState } from '../composables/useAsyncState'

const route = useRoute()
const profile = ref(null)
const followers = ref([])
const following = ref([])
const { loading, error, execute } = useAsyncState()
const { loading: followLoading, error: followError, execute: executeFollow } = useAsyncState()
loading.value = true

const username = computed(() => (typeof route.params.username === 'string' ? route.params.username : ''))

const isOwner = computed(() => authState.authenticated && authState.username === profile.value?.username)

const isFollowing = computed(() =>
  followers.value.some((entry) => entry.followerUsername === authState.username),
)

const initial = computed(() => profile.value.username?.slice(0, 1).toUpperCase() || 'U')

function formatDate(value) {
  if (!value) {
    return '-'
  }

  return new Intl.DateTimeFormat('pl-PL', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

async function loadProfile() {
  followError.value = ''
  const result = await execute(async () => {
    return await fetchUserProfile(username.value)
  }, { fallback: 'Nie udało się pobrać profilu.' })

  if (result) {
    profile.value = result
    if (authState.authenticated) {
      const [followersData, followingData] = await Promise.all([
        fetchFollowers(username.value),
        fetchFollowing(username.value),
      ])
      followers.value = followersData
      following.value = followingData
    } else {
      followers.value = []
      following.value = []
    }
  } else {
    profile.value = null
  }
}

async function toggleFollow() {
  const ok = await executeFollow(async () => {
    if (isFollowing.value) {
      await unfollowUser(username.value)
    } else {
      await followUser(username.value)
    }
    return true
  }, { fallback: 'Nie udało się zapisać obserwowania.' })
  if (ok) {
    followers.value = await fetchFollowers(username.value)
  }
}

onMounted(() => {
  loadProfile()
})

watch(
  () => route.params.username,
  () => {
    loadProfile()
  },
)
</script>
