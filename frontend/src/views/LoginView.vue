<template>
  <section class="mt-8 max-w-sm mx-auto">
    <h1 class="mb-6 text-center text-2xl font-bold">Zaloguj się</h1>

    <div v-if="route.query.registered" class="alert alert-success mb-4 text-sm">
      Konto zostało utworzone. Możesz się zalogować.
    </div>
    <div v-if="error" class="alert alert-error mb-4 text-sm">{{ error }}</div>

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <form class="space-y-4" @submit.prevent="submitLogin">
          <div class="form-control">
            <label class="label"><span class="label-text">Email</span></label>
            <input
              v-model="form.email"
              type="email"
              class="input input-bordered"
              placeholder="twoj@email.pl"
              autofocus
              required
            />
          </div>
          <div class="form-control">
            <label class="label"><span class="label-text">Hasło</span></label>
            <input
              v-model="form.password"
              type="password"
              class="input input-bordered"
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" class="btn btn-primary w-full" :disabled="loading">
            {{ loading ? 'Logowanie...' : 'Zaloguj' }}
          </button>
        </form>

        <p class="mt-4 text-center text-sm">
          Nie masz konta?
          <RouterLink to="/register" class="link link-primary">Zarejestruj się</RouterLink>
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { loginUser } from '../api'
import { refreshAuth } from '../auth'
import { useAsyncState } from '../composables/useAsyncState'

const route = useRoute()
const router = useRouter()
const { loading, error, execute } = useAsyncState()
const form = reactive({
  email: '',
  password: '',
})

async function submitLogin() {
  const ok = await execute(async () => {
    await loginUser({ email: form.email, password: form.password })
    return true
  }, { fallback: 'Nie udało się zalogować.' })
  if (!ok) return
  await refreshAuth()
  const nextPath = typeof route.query.next === 'string' ? route.query.next : '/'
  router.push(nextPath)
}
</script>
