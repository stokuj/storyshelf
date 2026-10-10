// Session = HttpOnly cookies (ADR-001); the SPA only knows who is logged in via /users/me/
import { queryOptions, useQuery } from '@tanstack/react-query'
import { api } from './client'

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
