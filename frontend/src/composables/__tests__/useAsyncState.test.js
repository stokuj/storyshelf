import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useAsyncState } from '../useAsyncState'

describe('useAsyncState', () => {
  it('initializes with loading=false, error="", message=""', () => {
    const { loading, error, message } = useAsyncState()

    expect(loading.value).toBe(false)
    expect(error.value).toBe('')
    expect(message.value).toBe('')
  })

  it('sets loading=true during execute()', async () => {
    let capturedLoading = false
    const { execute } = useAsyncState()

    const promise = execute(async () => {
      capturedLoading = true
      return 'done'
    })

    expect(capturedLoading).toBe(true)
    await promise
  })

  it('returns the result of the passed function', async () => {
    const { execute } = useAsyncState()

    const result = await execute(async () => 'hello')
    expect(result).toBe('hello')
  })

  it('sets error on rejection', async () => {
    const { execute, error } = useAsyncState()

    await execute(async () => {
      throw new Error('something went wrong')
    })

    expect(error.value).toBe('something went wrong')
  })

  it('uses fallback error message when error is not an Error instance', async () => {
    const { execute, error } = useAsyncState()

    await execute(async () => {
      throw 'raw string'
    }, { fallback: 'Fallback message' })

    expect(error.value).toBe('Fallback message')
  })

  it('clearFeedback() clears error and message', () => {
    const { error, message, clearFeedback } = useAsyncState()

    error.value = 'some error'
    message.value = 'some message'
    clearFeedback()

    expect(error.value).toBe('')
    expect(message.value).toBe('')
  })
})

describe('useAsyncState — timeout', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('sets error when fn exceeds timeout', async () => {
    const { loading, error, execute } = useAsyncState()

    const promise = execute(
      () => new Promise(() => {}), // never resolves
      { timeout: 1000, fallback: 'fallback error' },
    )

    vi.advanceTimersByTime(1100)
    await promise

    expect(loading.value).toBe(false)
    expect(error.value).toBe('Przekroczono czas oczekiwania.')
  })

  it('does not timeout when fn resolves in time', async () => {
    const { error, execute } = useAsyncState()

    const result = await execute(
      () => Promise.resolve('ok'),
      { timeout: 1000 },
    )

    expect(result).toBe('ok')
    expect(error.value).toBe('')
  })
})
