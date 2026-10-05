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
  expect((await screen.findByRole('alert')).textContent).toBe(
    'Missing template headings: Postacie',
  )
  expect(textarea.value).toBe(typed)
})

test('cancel discards unsaved text', async () => {
  renderApp('/books/krew-elfow?view=edit')
  edit(await source(), (v) => v + '\nNiezapisane.\n')
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
  await waitFor(() => expect(screen.queryByRole('textbox', { name: 'Page source' })).toBeNull())
  expect(screen.queryByText('Niezapisane.')).toBeNull()
  within(screen.getByRole('main')).getByRole('heading', { level: 1, name: 'Krew elfów' })
})
