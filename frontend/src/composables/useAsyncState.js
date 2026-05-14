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

    const timeout = options.timeout ?? 15000

    try {
      return await Promise.race([
        fn(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('__timeout__')), timeout),
        ),
      ])
    } catch (err) {
      if (err instanceof Error && err.message === '__timeout__') {
        error.value = 'Przekroczono czas oczekiwania.'
      } else {
        error.value = err instanceof Error ? err.message : options.fallback || 'Wystąpił błąd.'
      }
    } finally {
      loading.value = false
    }
  }

  return { loading, error, message, execute, clearFeedback }
}
