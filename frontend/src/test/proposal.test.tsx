import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  RouterProvider,
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router'
import { fireEvent, render, screen } from '@testing-library/react'
import { ProposalView } from '@/components/ProposalView'
import { FIXTURES, summary } from './mockWikiApi'

const OZ = '/books/ostatnie-zyczenie.md'
const page = { ...summary(OZ, FIXTURES[OZ]), content: FIXTURES[OZ], version: 1 }

// Links inside need a router: a one-route tree whose splat route renders the view
function show(proposalId: number) {
  const root = createRootRoute()
  const splat = createRoute({
    getParentRoute: () => root,
    path: '$',
    component: () => <ProposalView page={page} proposalId={proposalId} />,
  })
  const router = createRouter({
    routeTree: root.addChildren([splat]),
    history: createMemoryHistory({ initialEntries: ['/books/ostatnie-zyczenie'] }),
  })
  render(
    <QueryClientProvider client={new QueryClient()}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

test('an open proposal shows the prompt and the diff', async () => {
  show(1)
  await screen.findByText('Dodaj Nivellena do postaci')
  screen.getByText(/^\+ - \[Nivellen\]/)
})

test('accept marks the proposal accepted', async () => {
  show(1)
  fireEvent.click(await screen.findByRole('button', { name: /^Accept/ }))
  await screen.findByText('accepted')
  expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull()
})

test('reject marks the proposal rejected', async () => {
  show(1)
  fireEvent.click(await screen.findByRole('button', { name: 'Reject' }))
  await screen.findByText('rejected')
})

test('a stale proposal has accept disabled', async () => {
  show(2)
  const accept = (await screen.findByRole('button', { name: /^Accept/ })) as HTMLButtonElement
  expect(accept.disabled).toBe(true)
  screen.getByText('This page changed since the proposal was made.')
  expect(screen.queryByRole('button', { name: 'Reject' })).toBeNull()
})
