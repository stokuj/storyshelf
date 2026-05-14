import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

import { setTokens, clearTokens } from './api'

describe('api — token management', () => {
  it('setTokens stores access and refresh', () => {
    setTokens('acc123', 'ref456')
    expect(localStorage.getItem('access_token')).toBe('acc123')
    expect(localStorage.getItem('refresh_token')).toBe('ref456')
  })

  it('clearTokens removes both tokens', () => {
    localStorage.setItem('access_token', 'a')
    localStorage.setItem('refresh_token', 'b')
    clearTokens()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })
})

describe('api — 401 retry clears tokens when refresh produces no token', () => {
  it('throws "Session expired" and clears tokens when refresh returns empty access', async () => {
    localStorage.setItem('access_token', 'old-token')
    localStorage.setItem('refresh_token', 'old-refresh')

    // First call returns 401, second (refresh endpoint) returns access: null
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ access: null, refresh: null }),
      })

    const { fetchBooks } = await import('./api')
    await expect(fetchBooks()).rejects.toThrow('Session expired')
    expect(localStorage.getItem('access_token')).toBeNull()
  })
})
