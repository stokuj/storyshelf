import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

export function HomePage() {
  return (
    <main className="flex min-h-svh items-center justify-center">
      <h1 className="text-3xl font-semibold">StoryShelf</h1>
    </main>
  )
}
