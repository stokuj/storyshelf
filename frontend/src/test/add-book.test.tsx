import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

async function ask(prompt: string) {
  const input = await screen.findByRole('textbox', { name: 'Message to Agent' })
  fireEvent.change(input, { target: { value: prompt } })
  fireEvent.click(screen.getByRole('button', { name: 'Send' }))
}

test('confirming a candidate opens a new empty page listed in the sidebar', async () => {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'Add book' }))
  await ask('Lalka')
  const card = await screen.findByRole('article', { name: 'Lalka' })
  within(card).getByText('Bolesław Prus · 1890')
  fireEvent.click(within(card).getByRole('button', { name: 'Yes, add Lalka' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  const main = screen.getByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Lalka' })
  within(main).getByRole('heading', { name: 'Wątki i motywy' })
  within(main).getByText('draft')
  const nav = screen.getByRole('navigation', { name: 'Wiki' })
  await within(nav).findByRole('link', { name: 'Lalka' })
})

test('a double click on Yes, add creates the page once and opens it', async () => {
  const router = renderApp('/add')
  await ask('Lalka')
  const card = await screen.findByRole('article', { name: 'Lalka' })
  const add = within(card).getByRole('button', { name: 'Yes, add Lalka' })
  fireEvent.click(add)
  fireEvent.click(add)
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/lalka'))
  const posts = vi.mocked(fetch).mock.calls.filter(([, init]) => init?.method === 'POST')
  expect(posts).toHaveLength(1)
  expect(JSON.parse(posts[0][1]!.body as string)).toEqual({
    type: 'book',
    title: 'Lalka',
    author: 'Bolesław Prus',
    year: 1890,
  })
  expect(screen.queryByRole('alert')).toBeNull()
})

test('a candidate already in the wiki links to its page', async () => {
  renderApp('/add')
  await ask('Solaris')
  const card = await screen.findByRole('article', { name: 'Solaris' })
  expect(within(card).queryByRole('button', { name: /^Yes, add/ })).toBeNull()
  const link = within(card).getByRole('link', { name: 'Already in Wiki' })
  expect(link.getAttribute('href')).toBe('/books/solaris')
})

test('an unknown request falls back to the first three candidates', async () => {
  renderApp('/add')
  await ask('Dodaj wiedźmina tom 1')
  await screen.findByText("I'm not sure. Maybe one of these?")
  expect(screen.getAllByRole('article')).toHaveLength(3)
})

test('None of these hides the cards', async () => {
  renderApp('/add')
  await ask('Lalka')
  await screen.findByText('Is it one of these?')
  fireEvent.click(screen.getByRole('button', { name: 'None of these' }))
  screen.getByText('Try a different title or author.')
  expect(screen.queryByRole('article')).toBeNull()
})

test('a blank message cannot be sent', async () => {
  renderApp('/add')
  const input = await screen.findByRole('textbox', { name: 'Message to Agent' })
  fireEvent.change(input, { target: { value: '   ' } })
  expect((screen.getByRole('button', { name: 'Send' }) as HTMLButtonElement).disabled).toBe(true)
})

test('a draft page has no Generate button', async () => {
  renderApp('/characters/snaut--solaris')
  await screen.findByRole('heading', { level: 1, name: 'Snaut' })
  expect(screen.queryByRole('button', { name: /Generate/ })).toBeNull()
})
