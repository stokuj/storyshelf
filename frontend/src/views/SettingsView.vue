<template>
  <section class="max-w-lg mx-auto">
    <h1 class="mb-6 text-2xl font-bold">Ustawienia konta</h1>

    <div v-if="message" class="alert alert-success mb-4 text-sm">{{ message }}</div>
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>
    <div v-else-if="loading" class="py-20 text-center text-base-content/60">Ładowanie ustawień...</div>
    <div v-else-if="!authState.authenticated" class="alert alert-warning mb-4 text-sm">
      Zaloguj się, aby edytować ustawienia.
    </div>

    <div v-else-if="settings" class="card bg-base-100 shadow">
      <div class="card-body">
        <h2 class="card-title text-base">Konto</h2>
        <div class="form-control">
          <label class="label"><span class="label-text">Email</span></label>
          <input type="text" class="input input-bordered" :value="settings.email" disabled />
        </div>

        <div class="divider"></div>

        <h2 class="card-title text-base">Profil</h2>

        <div class="mb-4 flex items-center gap-3">
          <div class="avatar placeholder">
            <div class="w-12 rounded-full bg-base-200 text-base-content">
              <span>{{ settings.username.slice(0, 1).toUpperCase() }}</span>
            </div>
          </div>
          <div>
            <div class="font-semibold">{{ settings.username }}</div>
            <div class="text-xs text-base-content/60">
              Profil publiczny: {{ settings.profilePublic ? 'tak' : 'nie' }}
            </div>
          </div>
        </div>

        <form class="space-y-3" @submit.prevent="saveSettings">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Username</span>
              <span class="label-text-alt text-base-content/50">3-30 małych liter</span>
            </label>
            <input v-model="form.username" type="text" class="input input-bordered" pattern="[a-z]{3,30}" />
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">Bio</span></label>
            <textarea v-model="form.bio" class="textarea textarea-bordered" rows="4"></textarea>
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">Avatar URL</span></label>
            <input v-model="form.avatarUrl" type="text" class="input input-bordered" />
          </div>

          <div class="flex flex-wrap gap-2">
            <button type="submit" class="btn btn-primary btn-sm" :disabled="saving">
              {{ saving ? 'Zapisywanie...' : 'Zapisz profil' }}
            </button>
            <RouterLink :to="`/profile/${settings.username}`" class="btn btn-ghost btn-sm">Zobacz profil</RouterLink>
          </div>
        </form>

        <div class="divider"></div>

        <div class="flex items-center gap-3">
          <span class="text-sm">Widoczność profilu:</span>
          <button type="button" class="btn btn-outline btn-sm" :disabled="saving" @click="toggleVisibility">
            {{ settings.profilePublic ? 'Ustaw prywatny' : 'Ustaw publiczny' }}
          </button>
        </div>

        <div class="divider"></div>

        <h2 class="card-title text-base">Wyloguj się</h2>
        <p class="mb-3 text-sm text-base-content/60">Zakończ bieżącą sesję.</p>
        <button type="button" class="btn btn-outline btn-error btn-sm" @click="handleLogout">Wyloguj</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { fetchCurrentUserSettings, updateCurrentUserSettings, updateCurrentUserVisibility } from '../api'
import { authState, refreshAuth, signOut } from '../auth'

const router = useRouter()
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const message = ref('')
const settings = ref(null)
const form = reactive({
  username: '',
  bio: '',
  avatarUrl: '',
})

function syncForm(data) {
  form.username = data.username || ''
  form.bio = data.bio || ''
  form.avatarUrl = data.avatarUrl || ''
}

async function loadSettings() {
  loading.value = true
  error.value = ''

  try {
    await refreshAuth()
    if (!authState.authenticated) {
      settings.value = null
      return
    }

    settings.value = await fetchCurrentUserSettings()
    syncForm(settings.value)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się pobrać ustawień.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  error.value = ''
  message.value = ''

  try {
    settings.value = await updateCurrentUserSettings({ ...form })
    syncForm(settings.value)
    await refreshAuth()
    message.value = 'Zapisano zmiany profilu.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zapisać ustawień.'
  } finally {
    saving.value = false
  }
}

async function toggleVisibility() {
  if (!settings.value) {
    return
  }

  saving.value = true
  error.value = ''
  message.value = ''

  try {
    settings.value = await updateCurrentUserVisibility(!settings.value.profilePublic)
    syncForm(settings.value)
    message.value = 'Zmieniono widoczność profilu.'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Nie udało się zmienić widoczności.'
  } finally {
    saving.value = false
  }
}

async function handleLogout() {
  await signOut()
  router.push('/login')
}

onMounted(() => {
  loadSettings()
})
</script>
