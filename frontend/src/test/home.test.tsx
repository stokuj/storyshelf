import { render, screen } from '@testing-library/react'
import { HomePage } from '@/routes/index'

test('home page shows the app name', () => {
  render(<HomePage />)
  expect(screen.getByRole('heading', { name: 'StoryShelf' })).toBeInTheDocument()
})
