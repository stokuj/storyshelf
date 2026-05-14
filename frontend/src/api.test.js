import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('api — 401 retry with cookies', () => {
  beforeEach(() => {
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('retries request after 401 by calling refresh endpoint', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [{ id: 1, title: 'Dune' }],
      })

    const { fetchBooks } = await import('./api')
    const result = await fetchBooks()
    expect(result).toEqual([{ id: 1, title: 'Dune' }])
    expect(global.fetch).toHaveBeenCalledTimes(3)
    expect(global.fetch.mock.calls[1][0]).toBe('/api/auth/refresh/')
  })

  it('throws "Session expired" when refresh endpoint returns 401', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({ ok: false, status: 401 })

    const { fetchBooks } = await import('./api')
    await expect(fetchBooks()).rejects.toThrow('Session expired')
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('all requests include credentials: include', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    })

    const { fetchBooks } = await import('./api')
    await fetchBooks()
    expect(global.fetch.mock.calls[0][1]).toMatchObject({ credentials: 'include' })
  })
})
