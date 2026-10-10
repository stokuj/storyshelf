import { ApiError, api, apiErrorMessage } from './client'

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })

// Access token is "expired" until the refresh endpoint has been called
function stubServer({ refreshOk = true } = {}) {
  let refreshed = false
  const fetchMock = vi.fn(async (url: string) => {
    if (url === '/api/auth/refresh/') {
      refreshed = refreshOk
      return refreshOk ? json(200, { authenticated: true }) : json(401, { detail: 'expired' })
    }
    return refreshed ? json(200, { url }) : json(401, { detail: 'expired' })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

const refreshCalls = (f: ReturnType<typeof stubServer>) =>
  f.mock.calls.filter(([url]) => url === '/api/auth/refresh/').length

test('sends same-origin requests with cookies and a JSON body', async () => {
  const f = vi.fn(async () => json(201, { ok: true }))
  vi.stubGlobal('fetch', f)
  await api('/auth/login/', { method: 'POST', body: JSON.stringify({ a: 1 }) })
  expect(f).toHaveBeenCalledWith('/api/auth/login/', {
    method: 'POST',
    body: '{"a":1}',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  })
})

test('401 refreshes once and retries the original request', async () => {
  const f = stubServer()
  expect(await api('/users/me/')).toEqual({ url: '/api/users/me/' })
  expect(refreshCalls(f)).toBe(1)
  expect(f).toHaveBeenCalledTimes(3)
})

test('failed refresh throws ApiError 401', async () => {
  const f = stubServer({ refreshOk: false })
  const err = await api('/users/me/').catch((e: unknown) => e)
  expect(err).toBeInstanceOf(ApiError)
  expect((err as ApiError).status).toBe(401)
  expect(refreshCalls(f)).toBe(1)
})

test('parallel 401s share one refresh', async () => {
  const f = stubServer()
  await Promise.all([api('/a/'), api('/b/')])
  expect(refreshCalls(f)).toBe(1)
})

test('401 on an auth endpoint does not refresh', async () => {
  const f = stubServer()
  await expect(api('/auth/login/', { method: 'POST', body: '{}' })).rejects.toBeInstanceOf(ApiError)
  expect(refreshCalls(f)).toBe(0)
})

test('error body is parsed into ApiError.body', async () => {
  vi.stubGlobal('fetch', async () => json(400, { email: ['Enter a valid email address.'] }))
  const err = (await api('/auth/register/', { method: 'POST', body: '{}' }).catch(
    (e: unknown) => e,
  )) as ApiError
  expect(err.status).toBe(400)
  expect(err.body).toEqual({ email: ['Enter a valid email address.'] })
})

test.each([
  [
    400,
    { content: ['Missing template headings: Postacie'] },
    'Missing template headings: Postacie',
  ],
  [409, { detail: 'Page already exists.' }, 'Page already exists.'],
  [500, null, 'Something went wrong. Try again.'],
  [400, { content: [] }, 'Something went wrong. Try again.'],
])('apiErrorMessage %#', (status, body, message) => {
  expect(apiErrorMessage(new ApiError(status, body))).toBe(message)
})

test('apiErrorMessage of a non-API error is generic', () => {
  expect(apiErrorMessage(new TypeError('Failed to fetch'))).toBe('Something went wrong. Try again.')
})
