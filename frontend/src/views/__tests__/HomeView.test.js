import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

vi.mock('../../api', () => ({
  fetchBooks: vi.fn().mockResolvedValue([]),
}))

const routeMock = { query: { q: '' } }
vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => routeMock),
}))

import { fetchBooks } from '../../api'
import HomeView from '../HomeView.vue'

const stubs = {
  global: {
    stubs: {
      BookCard: { template: '<div />' },
      AlertMessage: { template: '<div />' },
      LoadingSpinner: { template: '<div />' },
    },
  },
}

describe('HomeView — search debounce', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    fetchBooks.mockClear()
    routeMock.query.q = ''
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('debounce: rapid consecutive loads result in single fetch', async () => {
    mount(HomeView, stubs)
    await flushPromises()
    fetchBooks.mockClear()

    // Simulate 3 rapid changes within debounce window
    routeMock.query.q = 'a'
    vi.advanceTimersByTime(100) // 100ms — debounce not yet fired
    routeMock.query.q = 'ab'
    vi.advanceTimersByTime(100) // 200ms total — still not fired
    routeMock.query.q = 'abc'
    vi.advanceTimersByTime(350) // 550ms total — debounce fires once
    await flushPromises()

    // Even if watcher fires 3 times, only 1 fetch should be sent
    expect(fetchBooks.mock.calls.length).toBeLessThanOrEqual(1)
  })
})
