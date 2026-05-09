async function parseError(response) {
  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    const data = await response.json().catch(() => null)
    if (data?.message) {
      return data.message
    }
    if (data?.error) {
      return data.error
    }
  }

  const text = await response.text().catch(() => '')
  return text || `Request failed with status ${response.status}`
}

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData
  const mergedHeaders = {
    ...(options.headers || {}),
  }

  if (!isFormData && !('Content-Type' in mergedHeaders)) {
    mergedHeaders['Content-Type'] = 'application/json'
  }

  const response = await fetch(path, {
    credentials: 'include',
    headers: mergedHeaders,
    ...options,
  })

  if (!response.ok) {
    throw new Error(await parseError(response))
  }

  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('application/json')) {
    return null
  }

  return response.json()
}

export function fetchBooks(query = '') {
  const url = new URL('/api/books', window.location.origin)
  if (query.trim()) {
    url.searchParams.set('q', query.trim())
  }

  return request(url.pathname + url.search, { method: 'GET' })
}

export function fetchAuthors() {
  return request('/api/authors', { method: 'GET' })
}

export function fetchSeries() {
  return request('/api/series', { method: 'GET' })
}

export function fetchBookDetails(bookId) {
  return request(`/api/books/${bookId}/details`, { method: 'GET' })
}

export function createBookReview(bookId, payload) {
  return request(`/api/books/${bookId}/reviews`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function loginUser(payload) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function registerUser(payload) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function fetchAuthMe() {
  return request('/api/auth/me', { method: 'GET' })
}

export function logoutUser() {
  return request('/api/auth/logout', { method: 'POST' })
}

export function fetchBookshelf() {
  return request('/api/shelf', { method: 'GET' })
}

export function fetchBookshelfEntry(bookId) {
  return request(`/api/shelf/${bookId}`, { method: 'GET' })
}

export function addToBookshelf(bookId, status = 'WANT_TO_READ') {
  return request(`/api/shelf/${bookId}`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export function updateBookshelfStatus(bookId, status) {
  return request(`/api/shelf/${bookId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function removeFromBookshelf(bookId) {
  return request(`/api/shelf/${bookId}`, { method: 'DELETE' })
}

export function fetchCurrentUserSettings() {
  return request('/api/users/me', { method: 'GET' })
}

export function fetchUserProfile(username) {
  return request(`/api/users/${encodeURIComponent(username)}`, { method: 'GET' })
}

export function fetchFollowers(username) {
  return request(`/api/users/${encodeURIComponent(username)}/followers`, { method: 'GET' })
}

export function fetchFollowing(username) {
  return request(`/api/users/${encodeURIComponent(username)}/following`, { method: 'GET' })
}

export function followUser(username) {
  return request(`/api/users/${encodeURIComponent(username)}/follow`, { method: 'POST' })
}

export function unfollowUser(username) {
  return request(`/api/users/${encodeURIComponent(username)}/follow`, { method: 'DELETE' })
}

export function updateCurrentUserSettings(payload) {
  return request('/api/users/me', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function updateCurrentUserVisibility(profilePublic) {
  const value = profilePublic ? 'true' : 'false'
  return request(`/api/users/me/visibility?profilePublic=${value}`, {
    method: 'PATCH',
  })
}

export function createModeratorBook(payload) {
  return request('/api/books', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function patchModeratorBook(bookId, payload) {
  return request(`/api/books/${bookId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteModeratorBook(bookId) {
  return request(`/api/books/${bookId}`, {
    method: 'DELETE',
  })
}

export function uploadModeratorBookContent(bookId, file) {
  const formData = new FormData()
  formData.append('file', file)

  return request(`/api/books/${bookId}/chapters`, {
    method: 'POST',
    body: formData,
  })
}

export function clearModeratorBookContent(bookId) {
  return request(`/api/books/${bookId}/chapters`, {
    method: 'DELETE',
  })
}

export function deleteModeratorReview(reviewId) {
  return request(`/api/reviews/${reviewId}`, {
    method: 'DELETE',
  })
}

export function createModeratorAuthor(payload) {
  return request('/api/authors', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateModeratorAuthor(authorId, payload) {
  return request(`/api/authors/${authorId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteModeratorAuthor(authorId) {
  return request(`/api/authors/${authorId}`, {
    method: 'DELETE',
  })
}

export function createModeratorSeries(payload) {
  return request('/api/series', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateModeratorSeries(seriesId, payload) {
  return request(`/api/series/${seriesId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteModeratorSeries(seriesId) {
  return request(`/api/series/${seriesId}`, {
    method: 'DELETE',
  })
}
