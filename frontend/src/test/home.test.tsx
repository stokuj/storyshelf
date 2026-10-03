import { render, screen } from '@testing-library/react'
import { Route } from '@/routes/index'

test('home page shows the app name', () => {
  const HomePage = Route.options.component!
  render(<HomePage />)
  screen.getByRole('heading', { name: 'StoryShelf' })
})
