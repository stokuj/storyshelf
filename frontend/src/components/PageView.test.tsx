import { render, screen } from '@testing-library/react'
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
      }}
    />,
  )
  screen.getByText('Bad source')
  expect(screen.queryByRole('link', { name: 'Bad source' })).toBeNull()
})
