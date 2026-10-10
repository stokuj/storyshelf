import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { json } from './mockFetch'
import { mockWikiApi } from './mockWikiApi'
import { renderApp } from './renderApp'

const fill = (name: string | RegExp, value: string) =>
  fireEvent.change(screen.getByRole('textbox', { name }), { target: { value } })
const pick = (name: string, value: string) =>
  fireEvent.change(screen.getByRole('combobox', { name }), { target: { value } })
const submit = () => fireEvent.click(screen.getByRole('button', { name: 'Create page' }))
const posts = () => vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === 'POST')
const postBody = () => JSON.parse(posts()[0][1]!.body as string) as unknown
const preview = (path: string) => screen.getByText(path, { selector: 'code' })

async function openNew() {
  const router = renderApp('/new')
  await screen.findByRole('heading', { level: 1, name: 'New page' })
  return router
}

async function openForm() {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'New page' }))
  await screen.findByRole('heading', { level: 1, name: 'New page' })
  return router
}

test('a book from the form opens as an empty draft Template listed in the sidebar', async () => {
  const router = await openForm()
  expect(router.state.location.pathname).toBe('/new')
  fill('Title', 'Sezon burz')
  preview('/books/sezon-burz.md')
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/sezon-burz'))
  const main = screen.getByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Sezon burz' })
  within(main).getByRole('heading', { name: 'Wątki i motywy' })
  within(main).getByText('draft')
})

test('a character needs a book; with one the body carries it', async () => {
  const router = await openNew()
  fireEvent.click(await screen.findByRole('radio', { name: 'Character' }))
  fill('Title', 'Ciri')
  const button = screen.getByRole('button', { name: 'Create page' }) as HTMLButtonElement
  expect(button.disabled).toBe(true)
  submit()
  expect(posts()).toHaveLength(0)
  await screen.findByRole('option', { name: 'Solaris' })
  pick('Book', '/books/krew-elfow.md')
  preview('/characters/ciri--krew-elfow.md')
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/characters/ciri--krew-elfow'))
  expect(postBody()).toEqual({ type: 'character', title: 'Ciri', book: '/books/krew-elfow.md' })
})

test('empty Author and Universe are omitted, Year is a number', async () => {
  const router = await openNew()
  fill('Title', 'Lalka')
  fireEvent.change(screen.getByRole('spinbutton', { name: /^Year/ }), { target: { value: '1890' } })
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  expect(postBody()).toEqual({ type: 'book', title: 'Lalka', year: 1890 })
})

test('switching the type does not send fields of the previous type', async () => {
  const router = await openNew()
  fill('Title', 'Ziemiomorze')
  fill(/^Author/, 'Ursula Le Guin')
  fireEvent.click(await screen.findByRole('radio', { name: 'Universe' }))
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/universes/ziemiomorze'))
  expect(postBody()).toEqual({ type: 'universe', title: 'Ziemiomorze' })
})

test('a taken Path shows the backend message and stays on the form', async () => {
  const router = await openNew()
  fill('Title', 'Solaris')
  submit()
  const alert = await screen.findByRole('alert')
  expect(alert.textContent).toBe('Page already exists: /books/solaris.md')
  expect(router.state.location.pathname).toBe('/new')
  expect((screen.getByRole('button', { name: 'Create page' }) as HTMLButtonElement).disabled).toBe(
    false,
  )
})

test('a double click creates the page once', async () => {
  const router = await openNew()
  fill('Title', 'Lalka')
  submit()
  submit()
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  expect(posts()).toHaveLength(1)
})

test('without books the Book list is disabled and says why', async () => {
  mockWikiApi({ 'GET /api/wiki/pages/': () => json(200, []) })
  await openNew()
  fireEvent.click(await screen.findByRole('radio', { name: 'Place' }))
  await screen.findByRole('option', { name: 'Add a book first' })
  expect((screen.getByRole('combobox', { name: 'Book' }) as HTMLSelectElement).disabled).toBe(true)
})
