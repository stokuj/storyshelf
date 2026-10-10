import { fireEvent, screen, waitFor } from '@testing-library/react'
import { safeRedirect } from '@/api/auth'
import { ME, json, mockFetch } from './mockFetch'
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

// The route renders async, so wait for the field before typing
const fill = async (label: string | RegExp, value: string) =>
  fireEvent.change(await screen.findByLabelText(label), { target: { value } })
// Submit the form itself: a submit event on the button does not reach React's onSubmit
const submit = (button: string) =>
  fireEvent.submit(screen.getByRole('button', { name: button }).closest('form')!)

// me is 401 until login/register succeeds
function server(authRoute: string, reply: () => Response) {
  let loggedIn = false
  return mockFetch({
    ...loggedOut,
    'GET /api/users/me/': () => (loggedIn ? json(200, ME) : json(401, { detail: 'no' })),
    [authRoute]: () => {
      const res = reply()
      loggedIn = res.ok
      return res
    },
  })
}

test('login lands on the redirect target and stores nothing in web storage', async () => {
  const f = server('POST /api/auth/login/', () => json(200, { authenticated: true }))
  const router = renderApp('/login?redirect=%2Fbooks%2Fsolaris')
  await fill('Email', 'stokuj@example.com')
  await fill('Password', 'secret123')
  submit('Log in')
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/solaris'))
  expect(f).toHaveBeenCalledWith(
    '/api/auth/login/',
    expect.objectContaining({ body: '{"email":"stokuj@example.com","password":"secret123"}' }),
  )
  expect(localStorage.length + sessionStorage.length).toBe(0)
})

test('wrong password shows the server message', async () => {
  server('POST /api/auth/login/', () =>
    json(400, { non_field_errors: ['Invalid email or password'] }),
  )
  renderApp('/login')
  await fill('Email', 'stokuj@example.com')
  await fill('Password', 'wrongpass')
  submit('Log in')
  expect((await screen.findByRole('alert')).textContent).toBe('Invalid email or password')
})

test('throttled login shows the detail message', async () => {
  server('POST /api/auth/login/', () =>
    json(429, { detail: 'Request was throttled. Expected available in 60 seconds.' }),
  )
  renderApp('/login')
  await fill('Email', 'stokuj@example.com')
  await fill('Password', 'secret123')
  submit('Log in')
  expect((await screen.findByRole('alert')).textContent).toMatch(/throttled/)
})

test('unsafe redirect target falls back to home', async () => {
  server('POST /api/auth/login/', () => json(200, { authenticated: true }))
  const router = renderApp('/login?redirect=%2F%2Fevil.com')
  await fill('Email', 'stokuj@example.com')
  await fill('Password', 'secret123')
  submit('Log in')
  await waitFor(() => expect(router.state.location.pathname).toBe('/'))
})

test.each([
  [undefined, '/'],
  ['/books/solaris?view=edit', '/books/solaris?view=edit'],
  ['//evil.com', '/'],
  ['/\\evil.com', '/'],
  ['https://evil.com', '/'],
  ['books', '/'],
])('safeRedirect(%s) is %s', (to, expected) => {
  expect(safeRedirect(to)).toBe(expected)
})

test('register shows field errors from the server', async () => {
  server('POST /api/auth/register/', () =>
    json(400, { handle: ['user with this handle already exists.'] }),
  )
  renderApp('/register')
  await fill('Email', 'new@example.com')
  await fill(/^Handle/, 'stokuj')
  await fill('Password', 'secret123')
  submit('Create account')
  await screen.findByText('user with this handle already exists.')
})

test('register logs in and lands on the wiki', async () => {
  server('POST /api/auth/register/', () =>
    json(201, { authenticated: true, email: 'new@example.com', handle: 'nowy' }),
  )
  const router = renderApp('/register')
  await fill('Email', 'new@example.com')
  await fill(/^Handle/, 'nowy')
  await fill('Password', 'secret123')
  submit('Create account')
  await waitFor(() => expect(router.state.location.pathname).toBe('/'))
  await screen.findByRole('navigation', { name: 'Wiki' })
})

test('login and register link to each other', async () => {
  const router = renderApp('/login')
  fireEvent.click(await screen.findByRole('link', { name: 'No account? Create one' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/register'))
  fireEvent.click(await screen.findByRole('link', { name: 'Have an account? Log in' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/login'))
})
