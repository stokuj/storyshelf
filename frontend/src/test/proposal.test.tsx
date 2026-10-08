import { fireEvent, screen, within } from '@testing-library/react'
import { getPage, savePage } from '@/api/store'
import { renderApp } from './renderApp'

const OZ = '/books/ostatnie-zyczenie.md'
const REVIEW = '/books/ostatnie-zyczenie?view=proposal&p=1'

const versionRows = async () =>
  within(await screen.findByRole('list', { name: 'Versions' })).getAllByRole('listitem')

test('the page links to its open proposal, which shows the diff', async () => {
  renderApp('/books/ostatnie-zyczenie')
  await screen.findByText(/Proposal: Dodaj Nivellena do postaci/)
  fireEvent.click(screen.getByRole('link', { name: 'Review' }))
  await screen.findByText('Dodaj Nivellena do postaci')
  screen.getByText(/^\+ - \[Nivellen\]/)
})

test('accept adds a proposal version and a verified event', async () => {
  renderApp(REVIEW)
  fireEvent.click(await screen.findByRole('button', { name: /^Accept/ }))
  await screen.findByText('Nivellen')
  screen.getByText(/verified by human:stokuj, human:stokuj/)
  expect(screen.queryByText(/Proposal: Dodaj Nivellena/)).toBeNull()
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  const rows = await versionRows()
  expect(rows).toHaveLength(4)
  within(rows[0]).getByText('Proposal')
})

test('reject leaves the page and history unchanged', async () => {
  const before = getPage(OZ).content
  renderApp(REVIEW)
  fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
  await screen.findByRole('link', { name: 'History' })
  expect(screen.queryByText(/Proposal: Dodaj Nivellena/)).toBeNull()
  expect(getPage(OZ).content).toBe(before)
  fireEvent.click(screen.getByRole('link', { name: 'History' }))
  expect(await versionRows()).toHaveLength(3)
})

test('after an edit the proposal is stale and accept is disabled', async () => {
  savePage(OZ, getPage(OZ).content + '\nDopisek.\n')
  renderApp(REVIEW)
  const accept = (await screen.findByRole('button', { name: /^Accept/ })) as HTMLButtonElement
  expect(accept.disabled).toBe(true)
  screen.getByText('This page changed since the proposal was made.')
  expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull()
})
