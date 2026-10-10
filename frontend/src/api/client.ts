// Same-origin JSON client (ADR-002); both JWTs live in HttpOnly cookies (ADR-001)
export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`API error ${status}`)
    this.status = status
    this.body = body
  }
}

const request = (path: string, init: RequestInit) =>
  fetch(`/api${path}`, {
    ...init,
    credentials: 'include',
    headers: init.body ? { 'Content-Type': 'application/json' } : undefined,
  })

// One refresh for every request that got 401 at once: refresh tokens rotate and
// the old one is blacklisted, so a second parallel refresh would log the user out
let refreshing: Promise<boolean> | null = null
function refresh() {
  refreshing ??= request('/auth/refresh/', { method: 'POST' })
    .then((r) => r.ok)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res = await request(path, init)
  if (res.status === 401 && !path.startsWith('/auth/') && (await refresh())) {
    res = await request(path, init)
  }
  const body: unknown = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, body)
  return body as T
}

const GENERIC_ERROR = 'Something went wrong. Try again.'

// One string for the UI: DRF 400 `{field: [msg]}` → first message, `{detail}` → detail, else generic
export function apiErrorMessage(e: unknown): string {
  if (!(e instanceof ApiError) || !e.body || typeof e.body !== 'object') return GENERIC_ERROR
  const { detail } = e.body as { detail?: unknown }
  if (typeof detail === 'string') return detail
  const first: unknown = Object.values(e.body)[0]
  return Array.isArray(first) && typeof first[0] === 'string' ? first[0] : GENERIC_ERROR
}
