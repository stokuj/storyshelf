import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { json } from './mockFetch'
import { FIXTURES, mockWikiApi } from './mockWikiApi'
import { renderApp } from './renderApp'

const KE = '/books/krew-elfow.md'
const STALE = 'This page changed since you opened it. Reload to get the latest version.'

const source = async () =>
  (await screen.findByRole('textbox', { name: 'Page source' })) as HTMLTextAreaElement
const append = (textarea: HTMLTextAreaElement, text: string) =>
  fireEvent.change(textarea, { target: { value: textarea.value + text } })
const save = () => fireEvent.click(screen.getByRole('button', { name: 'Save' }))

test('400 shows the backend message, keeps the text and clears on typing', async () => {
  mockWikiApi({
    [`PUT /api/wiki/pages${KE}`]: () =>
      json(400, { content: ['Missing template headings: Postacie'] }),
  })
  renderApp('/books/krew-elfow?view=edit')
  const textarea = await source()
  append(textarea, '\nZmiana.\n')
  const typed = textarea.value
  save()
  expect((await screen.findByRole('alert')).textContent).toBe('Missing template headings: Postacie')
  expect(textarea.value).toBe(typed)
  append(textarea, 'x')
  expect(screen.queryByRole('alert')).toBeNull()
})

test('409 asks to reload, and Reload loads the newer text', async () => {
  const { write } = mockWikiApi()
  renderApp('/books/krew-elfow?view=edit')
  const textarea = await source()
  write(KE, FIXTURES[KE] + '\nZmiana obca.\n') // someone else saved first
  append(textarea, '\nMoja zmiana.\n')
  save()
  expect((await screen.findByRole('alert')).textContent).toBe(STALE)

  fireEvent.click(screen.getByRole('button', { name: 'Reload' }))
  await waitFor(() => expect(textarea.value).toContain('Zmiana obca.'))
  expect(textarea.value).not.toContain('Moja zmiana.')
  expect(screen.queryByRole('alert')).toBeNull()

  save()
  await screen.findByText('Zmiana obca.')
  expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull()
})

test('Reload during an outage keeps the text and the stale message', async () => {
  const overrides: Record<string, () => Response> = {}
  const { write } = mockWikiApi(overrides)
  renderApp('/books/krew-elfow?view=edit')
  const textarea = await source()
  write(KE, FIXTURES[KE] + '\nZmiana obca.\n')
  append(textarea, '\nMoja zmiana.\n')
  const typed = textarea.value
  save()
  expect((await screen.findByRole('alert')).textContent).toBe(STALE)

  overrides[`GET /api/wiki/pages${KE}`] = () => json(500, null)
  fireEvent.click(screen.getByRole('button', { name: 'Reload' }))
  // The failed refetch is retried once (1 s) before it settles
  await new Promise((r) => setTimeout(r, 1500))
  expect(textarea.value).toBe(typed)
  expect(screen.getByRole('alert').textContent).toBe(STALE)
})

test('a missing page says not found and is not retried', async () => {
  renderApp('/books/nope')
  await screen.findByText(/^Page not found\./)
  const calls = vi
    .mocked(fetch)
    .mock.calls.filter(([url]) => url === '/api/wiki/pages/books/nope.md')
  expect(calls).toHaveLength(1)
})

test('a server error on a page is not "not found"', async () => {
  mockWikiApi({ 'GET /api/wiki/pages/books/solaris.md': () => json(500, null) })
  renderApp('/books/solaris')
  // One retry (1 s) before the error shows
  await screen.findByText(/^Could not load this page\./, {}, { timeout: 3000 })
  expect(screen.queryByText(/^Page not found\./)).toBeNull()
})

test('a failed page list shows an alert in the sidebar', async () => {
  mockWikiApi({ 'GET /api/wiki/pages/': () => json(500, null) })
  renderApp('/')
  const nav = await screen.findByRole('navigation', { name: 'Wiki' })
  expect((await within(nav).findByRole('alert')).textContent).toBe('Could not load pages.')
})

test('a failed Yes, add shows the backend detail and can be retried', async () => {
  mockWikiApi({
    'POST /api/wiki/pages/': () => json(409, { detail: 'Page already exists: /books/lalka.md' }),
  })
  renderApp('/add')
  fireEvent.change(await screen.findByRole('textbox', { name: 'Message to Agent' }), {
    target: { value: 'Lalka' },
  })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))
  const card = await screen.findByRole('article', { name: 'Lalka' })
  const add = within(card).getByRole('button', { name: 'Yes, add Lalka' }) as HTMLButtonElement
  fireEvent.click(add)
  expect((await within(card).findByRole('alert')).textContent).toBe(
    'Page already exists: /books/lalka.md',
  )
  expect(add.disabled).toBe(false)
})

test('a refetch that moved the page on does not let Save overwrite it', async () => {
  const { write } = mockWikiApi()
  const router = renderApp('/books/krew-elfow?view=edit')
  const textarea = await source()
  write(KE, FIXTURES[KE] + '\nZmiana obca.\n')
  await router.options.context.queryClient.refetchQueries({ queryKey: ['page', KE] })
  append(textarea, '\nMoja zmiana.\n')
  save()
  expect((await screen.findByRole('alert')).textContent).toBe(STALE)
})

test('a failed refetch keeps the editor and its text', async () => {
  const overrides: Parameters<typeof mockWikiApi>[0] = {}
  mockWikiApi(overrides)
  const router = renderApp('/books/krew-elfow?view=edit')
  const textarea = await source()
  append(textarea, '\nMoja zmiana.\n')
  overrides[`GET /api/wiki/pages${KE}`] = () => json(500, null)
  await router.options.context.queryClient.refetchQueries({ queryKey: ['page', KE] })
  expect(screen.queryByText(/Could not load this page/)).toBeNull()
  expect(textarea.value).toContain('Moja zmiana.')
})
