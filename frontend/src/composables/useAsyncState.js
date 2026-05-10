import { ref } from 'vue'

export function useAsyncState() {
  const loading = ref(false)
  const error = ref('')
  const message = ref('')

  function clearFeedback() {
    error.value = ''
    message.value = ''
  }

  async function execute(fn, options = {}) {
    loading.value = true
    error.value = ''
    message.value = ''

    try {
      return await fn()
    } catch (err) {
      error.value = err instanceof Error ? err.message : options.fallback || 'Wystąpił błąd.'
    } finally {
      loading.value = false
    }
  }

  return { loading, error, message, execute, clearFeedback }
}
