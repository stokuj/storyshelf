import { screen, waitFor } from '@testing-library/react'
import { json, mockFetch } from './mockFetch'
import { renderApp } from './renderApp'

const loggedOut = {
  'GET /api/users/me/': () =>
    json(401, { detail: 'Authentication credentials were not provided.' }),
  'POST /api/auth/refresh/': () => json(401, { detail: 'Refresh token not found.' }),
}

test('logged-out user on a wiki route is sent to login', async () => {
  mockFetch(loggedOut)
  const router = renderApp('/books/solaris')
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
  expect(router.state.location.search).toEqual({ redirect: '/books/solaris' })
  await screen.findByRole('heading', { name: 'Log in' })
  expect(screen.queryByRole('navigation', { name: 'Wiki' })).toBeNull()
})

test('logged-in user stays on the wiki route', async () => {
  const router = renderApp('/books/solaris')
  await screen.findByRole('heading', { level: 1, name: 'Solaris' })
  expect(router.state.location.pathname).toBe('/books/solaris')
})

test('server error on me is not a login redirect', async () => {
  mockFetch({ 'GET /api/users/me/': () => json(500, null) })
  const router = renderApp('/')
  // Router shows its default error component; the URL stays put
  await screen.findByText(/something went wrong/i)
  expect(router.state.location.pathname).toBe('/')
})
