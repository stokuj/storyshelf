import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return <p className="text-muted-foreground">Pick a page from the sidebar.</p>
}
