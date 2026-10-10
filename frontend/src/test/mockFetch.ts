import type { Me } from '@/api/auth'

export const ME: Me = {
  id: 1,
  handle: 'stokuj',
  display_name: '',
  email: 'stokuj@example.com',
  bio: '',
  avatar_url: null,
  member_since: '2026-01-01T00:00:00Z',
  profile_public: true,
}

export const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

type Route = (init?: RequestInit) => Response

// Stubs fetch with 'METHOD /api/path' routes on top of a logged-in User; anything else is 404
export function mockFetch(routes: Record<string, Route> = {}) {
  const all: Record<string, Route> = { 'GET /api/users/me/': () => json(200, ME), ...routes }
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    const route = all[`${init?.method ?? 'GET'} ${url}`]
    return route ? route(init) : json(404, { detail: 'Not found.' })
  })
  vi.stubGlobal('fetch', fn)
  return fn
}
