<template>
  <section class="mt-8 max-w-sm mx-auto">
    <h1 class="mb-6 text-center text-2xl font-bold">Utwórz konto</h1>

    <AlertMessage v-if="error" :message="error" class="mb-4" />

    <div class="card bg-base-100 shadow">
      <div class="card-body">
        <form class="space-y-4" @submit.prevent="submitRegister">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Username</span>
              <span class="label-text-alt text-base-content/50">3-30 małych liter</span>
            </label>
            <input
              v-model="form.username"
              type="text"
              class="input input-bordered"
              placeholder="twojnick"
              pattern="[a-z]{3,30}"
              required
            />
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">Email</span></label>
            <input
              v-model="form.email"
              type="email"
              class="input input-bordered"
              placeholder="twoj@email.pl"
              required
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Hasło</span>
              <span class="label-text-alt text-base-content/50">min. 6 znaków</span>
            </label>
            <input
              v-model="form.password"
              type="password"
              class="input input-bordered"
              placeholder="••••••••"
              minlength="6"
              required
            />
          </div>

          <div class="form-control">
            <label class="label"><span class="label-text">Potwierdź hasło</span></label>
            <input
              v-model="confirmPassword"
              type="password"
              class="input input-bordered"
              placeholder="••••••••"
              minlength="6"
              required
            />
          </div>

          <button type="submit" class="btn btn-primary w-full" :disabled="loading">
            {{ loading ? 'Rejestrowanie...' : 'Zarejestruj się' }}
          </button>
        </form>

        <p class="mt-4 text-center text-sm">
          Masz już konto?
          <RouterLink to="/login" class="link link-primary">Zaloguj się</RouterLink>
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { registerUser } from '../api'
import { useAsyncState } from '../composables/useAsyncState'
import AlertMessage from '../components/AlertMessage.vue'

const router = useRouter()
const { loading, error, execute } = useAsyncState()
const confirmPassword = ref('')
const form = reactive({
  username: '',
  email: '',
  password: '',
})

async function submitRegister() {
  if (form.password !== confirmPassword.value) {
    error.value = 'Hasła nie są identyczne.'
    return
  }
  const ok = await execute(async () => {
    await registerUser(form)
    return true
  }, { fallback: 'Nie udało się utworzyć konta.' })
  if (!ok) return
  router.push('/login?registered=1')
}
</script>
