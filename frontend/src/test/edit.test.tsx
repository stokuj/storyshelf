import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const source = async () =>
  (await screen.findByRole('textbox', { name: 'Page source' })) as HTMLTextAreaElement

function edit(textarea: HTMLTextAreaElement, change: (value: string) => string) {
  fireEvent.change(textarea, { target: { value: change(textarea.value) } })
}

test('Edit opens the editor with the raw page source', async () => {
  renderApp('/books/krew-elfow')
  fireEvent.click(await screen.findByRole('link', { name: 'Edit' }))
  expect((await source()).value.startsWith('---\ntype: book\n')).toBe(true)
})

test('saving an edit shows the new content', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) =>
    v.replace('## Wątki i motywy', '## Wątki i motywy\n\nDopisek z edycji.'),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await screen.findByText('Dopisek z edycji.')
  expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull()
})

test('removing a template heading blocks save and keeps the text', async () => {
  renderApp('/books/solaris?view=edit')
  const textarea = await source()
  edit(textarea, (v) => v.replace('## Postacie\n', ''))
  const typed = textarea.value
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  expect((await screen.findByRole('alert')).textContent).toBe('Missing template headings: Postacie')
  expect(textarea.value).toBe(typed)
  edit(textarea, (v) => v + '\n')
  expect(screen.queryByRole('alert')).toBeNull()
})

test('cancel discards unsaved text', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) => v + '\nNiezapisane.\n')
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
  await waitFor(() => expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull())
  expect(screen.queryByText('Niezapisane.')).toBeNull()
  within(screen.getByRole('main')).getByRole('heading', { level: 1, name: 'Krew elfów' })
})

const versionRows = async () =>
  within(await screen.findByRole('list', { name: 'Versions' })).getAllByRole('listitem')

test('an edit appears on top of history', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) =>
    v.replace('## Wątki i motywy', '## Wątki i motywy\n\nDopisek z edycji.'),
  )
  fireEvent.click(screen.getByRole('button', { name: 'Save' }))
  await screen.findByText('Dopisek z edycji.')
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  const rows = await versionRows()
  expect(rows).toHaveLength(2)
  within(rows[0]).getByText('v2')
  within(rows[0]).getByText('Edit')
  within(rows[1]).getByText('Generation')
})

test('viewing an old version shows it read-only', async () => {
  renderApp('/books/ostatnie-zyczenie?view=history')
  const rows = await versionRows()
  expect(rows.map((r) => within(r).getByText(/^v\d+$/).textContent)).toEqual(['v3', 'v2', 'v1'])
  fireEvent.click(within(rows[2]).getByRole('link', { name: 'View' }))
  await screen.findByText(/Viewing v1 · Created/)
  screen.getByRole('heading', { level: 2, name: 'Streszczenie' })
  expect(screen.queryByText(/Ranny Geralt/)).toBeNull()
  expect(screen.queryByRole('link', { name: 'Edit' })).toBeNull()
})

test.each(['999', 'abc'])('version id %s shows not found with a way back', async (v) => {
  renderApp(`/books/ostatnie-zyczenie?view=history&v=${v}`)
  await screen.findByText(/^Version not found\./)
  screen.getByRole('link', { name: 'History' })
})

test('an unknown view falls back to the page', async () => {
  renderApp('/books/ostatnie-zyczenie?view=bogus')
  await screen.findByRole('link', { name: 'Edit' })
})
