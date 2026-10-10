// Session = HttpOnly cookies (ADR-001); the SPA only knows who is logged in via /users/me/
import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { ApiError, api } from './client'

// GET /api/users/me/ (UserMeSerializer)
export interface Me {
  id: number
  handle: string
  display_name: string
  email: string
  bio: string
  avatar_url: string | null
  member_since: string
  profile_public: boolean
}

export const meQuery = queryOptions({
  queryKey: ['me'],
  queryFn: () => api<Me>('/users/me/'),
  // 'me' changes only on login, register and logout, which reset it explicitly
  retry: false,
  staleTime: Infinity,
})

export const useMe = () => useQuery(meQuery)

const post = (path: string, data: unknown) =>
  api(path, { method: 'POST', body: JSON.stringify(data) })

// Only paths inside the app: '//evil.com', '/\evil.com' or 'https://…' would leave it
export const safeRedirect = (to?: string) => (to && /^\/(?![/\\])/.test(to) ? to : '/')

export interface Credentials {
  email: string
  password: string
}

// A new session: drop any cached 'me' so the guard fetches the new User
function useSessionMutation<V>(path: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: V) => post(path, data),
    onSuccess: () => qc.removeQueries({ queryKey: ['me'] }),
  })
}

export const useLogin = () => useSessionMutation<Credentials>('/auth/login/')

// DRF errors: { field: [msg] } per field; non_field_errors / detail belong to the whole form
export function formErrors(error: unknown): Record<string, string> {
  if (!error) return {}
  if (!(error instanceof ApiError) || !error.body || typeof error.body !== 'object') {
    return { form: 'Something went wrong. Try again.' }
  }
  const out: Record<string, string> = {}
  for (const [key, value] of Object.entries(error.body)) {
    const name = key === 'non_field_errors' || key === 'detail' ? 'form' : key
    out[name] = Array.isArray(value) ? value.join(' ') : String(value)
  }
  return out
}

// The backend sets the session cookies on register too
export const useRegister = () =>
  useSessionMutation<Credentials & { handle: string }>('/auth/register/')

export function useLogout() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  return useMutation({
    mutationFn: () => api('/auth/logout/', { method: 'POST' }),
    // Leave the wiki first so no mounted query refetches as a logged-out user
    onSuccess: async () => {
      await navigate({ to: '/login' })
      qc.clear()
    },
  })
}
