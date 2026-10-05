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
