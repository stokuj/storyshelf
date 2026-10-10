import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import { FIXTURES, mockWikiApi } from '@/test/mockWikiApi'
import { renderApp } from '@/test/renderApp'
import { PageView } from './PageView'

test('unsafe source URL renders as plain text', () => {
  const content = [
    '---',
    'type: book',
    'title: Evil',
    'sources:',
    '  - { id: x, resource: "javascript:alert(1)", title: Bad source }',
    '---',
    '',
    '## Body',
  ].join('\n')
  render(
    <PageView
      page={{
        path: '/books/evil.md',
        type: 'book',
        title: 'Evil',
        book: null,
        universe: null,
        content,
        version: 1,
      }}
    />,
  )
  screen.getByText('Bad source')
  expect(screen.queryByRole('link', { name: 'Bad source' })).toBeNull()
})

test('body links: a sanitised href is text, a #fragment stays on the page', async () => {
  const content = [
    '---',
    'type: book',
    'title: Links',
    '---',
    '',
    '[Bad](javascript:alert(1)) [Anchor](#top)',
  ].join('\n')
  const page = { path: '/books/links.md', type: 'book' as const, title: 'Links', book: null }
  render(
    <QueryClientProvider client={new QueryClient()}>
      <PageView page={{ ...page, universe: null, content, version: 1 }} />
    </QueryClientProvider>,
  )
  expect(screen.queryByRole('link', { name: 'Bad' })).toBeNull()
  screen.getByText('Bad')
  const anchor = screen.getByRole('link', { name: 'Anchor' })
  expect(anchor.getAttribute('href')).toBe('#top')
  expect(anchor.getAttribute('target')).toBeNull()
})

test('a wiki link with a #fragment resolves to the Page', async () => {
  const path = '/universes/wiedzmin.md'
  mockWikiApi().write(path, `${FIXTURES[path]}\n[Solaris](/books/solaris.md#plot)\n`)
  renderApp('/universes/wiedzmin')
  const main = await screen.findByRole('main')
  const link = await within(main).findByRole('link', { name: 'Solaris' })
  expect(link.getAttribute('href')).toBe('/books/solaris')
})
