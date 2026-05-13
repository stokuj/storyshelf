export function setTokens(access, refresh) {
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

function getAccessToken() {
  return localStorage.getItem('access_token')
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) throw new Error('no refresh token')
  const res = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) throw new Error('refresh failed')
  const data = await res.json()
  setTokens(data.access, data.refresh)
  return data.access
}

async function request(method, path, body, isFormData = false) {
  const headers = {}
  if (!isFormData) headers['Content-Type'] = 'application/json'
  const accessToken = getAccessToken()
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  let res
  try {
    res = await fetch(path, {
      method,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('Brak połączenia z serwerem.')
  }

  if (res.status === 401 && accessToken) {
    try {
      await refreshAccessToken()
      headers['Authorization'] = `Bearer ${getAccessToken()}`
      res = await fetch(path, {
        method,
        headers,
        body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      })
    } catch {
      clearTokens()
      throw new Error('Session expired')
    }
  }

  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) {
    const msg = data.detail || data.message || data.error || res.statusText
    throw new Error(msg)
  }
  return data
}

export function fetchBooks(query = '') {
  const url = new URL('/api/books/', window.location.origin)
  if (query.trim()) {
    url.searchParams.set('q', query.trim())
  }
  return request('GET', url.pathname + url.search)
}

export function fetchBookDetails(bookId) {
  return request('GET', `/api/books/${bookId}/`)
}

export function fetchReviews(bookId) {
  return request('GET', `/api/reviews/?book_id=${bookId}`)
}

export function createReview(payload) {
  return request('POST', '/api/reviews/', payload)
}

export function deleteReview(reviewId) {
  return request('DELETE', `/api/reviews/${reviewId}/`)
}

export function updateReview(reviewId, payload) {
  return request('PATCH', `/api/reviews/${reviewId}/`, payload)
}

export async function loginUser(payload) {
  const data = await request('POST', '/api/auth/login/', payload)
  setTokens(data.access, data.refresh)
  return data
}

export async function registerUser(payload) {
  const data = await request('POST', '/api/auth/register/', payload)
  setTokens(data.access, data.refresh)
  return data
}

export function fetchAuthMe() {
  return request('GET', '/api/auth/me/')
}

export async function logoutUser() {
  try {
    await request('POST', '/api/auth/logout/', { refresh: localStorage.getItem('refresh_token') })
  } finally {
    clearTokens()
  }
}

export function fetchBookshelf() {
  return request('GET', '/api/shelf/')
}

export function addToBookshelf(bookId, status = 'WANT_TO_READ') {
  return request('POST', `/api/shelf/${bookId}/`, { status })
}

export function updateBookshelfStatus(bookId, status) {
  return request('PATCH', `/api/shelf/${bookId}/`, { status })
}

export function removeFromBookshelf(bookId) {
  return request('DELETE', `/api/shelf/${bookId}/`)
}

export function fetchCurrentUserSettings() {
  return request('GET', '/api/users/me/')
}

export function fetchUserProfile(username) {
  return request('GET', `/api/users/${encodeURIComponent(username)}/`)
}

export function fetchFollowers(username) {
  return request('GET', `/api/users/${encodeURIComponent(username)}/followers/`)
}

export function fetchFollowing(username) {
  return request('GET', `/api/users/${encodeURIComponent(username)}/following/`)
}

export function followUser(username) {
  return request('POST', `/api/users/${encodeURIComponent(username)}/follow/`)
}

export function unfollowUser(username) {
  return request('DELETE', `/api/users/${encodeURIComponent(username)}/follow/`)
}

export function updateCurrentUserSettings(payload) {
  return request('PUT', '/api/users/me/', payload)
}

export function updateCurrentUserVisibility(profilePublic) {
  const value = profilePublic ? 'true' : 'false'
  return request('PATCH', `/api/users/me/visibility/?profilePublic=${value}`)
}


