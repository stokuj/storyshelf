import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

// queryClient in the context lets beforeLoad guards read cached queries
export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: Outlet,
})
