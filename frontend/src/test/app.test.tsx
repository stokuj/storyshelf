import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const section = (root: HTMLElement, name: string) =>
  within(root).getByRole('heading', { name }).closest('section')!

test('home shows the sidebar and an empty state', async () => {
  renderApp('/')
  await screen.findByText('Pick a page from the sidebar.')
  screen.getByRole('navigation', { name: 'Wiki' })
})

test('sidebar lists every page grouped by type', async () => {
  renderApp('/')
  const nav = await screen.findByRole('navigation', { name: 'Wiki' })
  await within(nav).findByRole('link', { name: 'Solaris' })
  for (const [label, count] of [
    ['Books', 3],
    ['Characters', 8],
    ['Places', 3],
    ['Universes', 1],
  ] as const) {
    expect(within(section(nav, `${label} ${count}`)).getAllByRole('link')).toHaveLength(count)
  }
  // Same character in two books is told apart by the book title
  within(nav).getByRole('link', { name: 'Geralt z Rivii Krew elfów' })
  within(nav).getByRole('link', { name: 'Geralt z Rivii Ostatnie życzenie' })
})

test('clicking a page opens its path and highlights only it', async () => {
  const router = renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: 'Krew elfów' }))
  await waitFor(() => expect(router.state.location.pathname).toBe('/books/krew-elfow'))
  await screen.findByRole('heading', { level: 1, name: 'Krew elfów' })
  expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
  const link = screen.getByRole('link', { name: 'Krew elfów' })
  expect(link.getAttribute('aria-current')).toBe('page')
})

test('universe page lists its books, characters and places', async () => {
  renderApp('/universes/wiedzmin')
  const main = await screen.findByRole('main')
  await within(main).findByRole('heading', { name: 'Books in this universe' })
  expect(within(section(main, 'Books in this universe')).getAllByRole('link')).toHaveLength(2)
  expect(within(section(main, 'Characters in this universe')).getAllByRole('link')).toHaveLength(5)
  expect(within(section(main, 'Places in this universe')).getAllByRole('link')).toHaveLength(2)
  expect(within(main).queryByText(/Solaris/)).toBeNull()
})

test('unknown path shows not found inside the frame', async () => {
  renderApp('/books/nope')
  await screen.findByText('Page not found.')
  screen.getByRole('navigation', { name: 'Wiki' })
})

test.each([
  ['/books/ostatnie-zyczenie', 'Ostatnie życzenie'],
  ['/characters/renfri--ostatnie-zyczenie', 'Renfri'],
  ['/places/blaviken--ostatnie-zyczenie', 'Blaviken'],
  ['/universes/wiedzmin', 'Wiedźmin'],
])('%s renders header and body', async (url, title) => {
  renderApp(url)
  const main = await screen.findByRole('main')
  await within(main).findByRole('heading', { level: 1, name: title })
  expect(within(main).getAllByRole('heading', { level: 2 }).length).toBeGreaterThan(0)
})

test('book footer shows sources and verification', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const footer = await screen.findByRole('contentinfo')
  const source = within(footer).getByRole('link', { name: 'Ostatnie życzenie — Wikipedia' })
  expect(source.getAttribute('target')).toBe('_blank')
  expect(source.getAttribute('rel')).toBe('noopener noreferrer')
  within(footer).getByText(/human:stokuj/)
  expect(within(screen.getByRole('main')).queryByText('draft')).toBeNull()
})

test('draft page shows its status and no footer', async () => {
  renderApp('/characters/snaut--solaris')
  const main = await screen.findByRole('main')
  await within(main).findByRole('heading', { level: 1, name: 'Snaut' })
  within(main).getByText('draft')
  expect(within(main).queryByRole('contentinfo')).toBeNull()
})

const pageBody = async (heading: string) =>
  (await screen.findByRole('heading', { level: 2, name: heading })).closest(
    '.page-body',
  ) as HTMLElement

test('mentions render as badges by page type', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const body = await pageBody('Postacie')
  for (const name of ['Geralt z Rivii', 'Jaskier', 'Yennefer z Vengerbergu', 'Renfri']) {
    expect(within(body).getByRole('link', { name }).className).toContain('bg-character')
  }
  expect(within(body).getByRole('link', { name: 'Blaviken' }).className).toContain('bg-place')
})

test('clicking a badge opens that page', async () => {
  const router = renderApp('/books/ostatnie-zyczenie')
  const main = await screen.findByRole('main')
  fireEvent.click(await within(main).findByRole('link', { name: 'Renfri' }))
  await waitFor(() =>
    expect(router.state.location.pathname).toBe('/characters/renfri--ostatnie-zyczenie'),
  )
  await within(main).findByRole('heading', { level: 1, name: 'Renfri' })
})

test('link to a missing page renders as plain text', async () => {
  renderApp('/books/ostatnie-zyczenie')
  const main = await screen.findByRole('main')
  await within(main).findByText('Nenneke')
  expect(within(main).queryByRole('link', { name: 'Nenneke' })).toBeNull()
})

test('book and external links in the body are plain links', async () => {
  renderApp('/universes/wiedzmin')
  const body = await pageBody('Opis')
  const book = within(body).getByRole('link', { name: 'Ostatniego życzenia' })
  expect(book.getAttribute('href')).toBe('/books/ostatnie-zyczenie')
  expect(book.className).not.toContain('bg-')
  const external = within(body).getByRole('link', { name: 'Wikipedii' })
  expect(external.getAttribute('target')).toBe('_blank')
  expect(external.getAttribute('rel')).toBe('noopener noreferrer')
})
