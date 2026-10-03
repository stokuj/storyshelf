import { render, screen } from '@testing-library/react'
import { Route } from '@/routes/index'

test('home page shows the app name', async () => {
  // autoCodeSplitting makes the route component lazy; load it before rendering
  const HomePage = Route.options.component!
  await HomePage.preload?.()
  render(<HomePage />)
  expect(screen.getByRole('heading', { name: 'StoryShelf' })).toBeInTheDocument()
})
