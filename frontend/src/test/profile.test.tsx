import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { renderApp } from './renderApp'

const cards = (name: string) =>
  within(screen.getByRole('heading', { name }).closest('section')!).getAllByRole('listitem')

test('profile shows about, the public switch and favourite cards', async () => {
  renderApp('/')
  fireEvent.click(await screen.findByRole('link', { name: '@stokuj' }))
  await screen.findByRole('heading', { level: 1, name: '@stokuj' })
  screen.getByText('Czytam fantastykę, głównie polską.')
  expect(cards('Favourite books')).toHaveLength(2)
  expect(cards('Favourite characters')).toHaveLength(1)
  screen.getByText('Wiedźmin, łowca potworów ze szkoły Wilka.')
  expect(within(screen.getByRole('main')).queryAllByRole('link')).toHaveLength(0)
})

test('the public switch toggles visibility', async () => {
  renderApp('/profile')
  const toggle = (await screen.findByRole('switch', {
    name: 'Public profile',
  })) as HTMLInputElement
  expect(toggle.checked).toBe(true)
  fireEvent.click(toggle)
  await waitFor(() => expect(toggle.checked).toBe(false))
})
