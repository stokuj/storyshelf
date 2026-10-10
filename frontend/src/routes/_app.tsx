// Pathless layout for every wiki route: logged-out users go to /login
import { Outlet, createFileRoute, redirect } from '@tanstack/react-router'
import { meQuery } from '@/api/auth'
import { ApiError } from '@/api/client'
import { Sidebar } from '@/components/Sidebar'

export const Route = createFileRoute('/_app')({
  beforeLoad: async ({ context, location }) => {
    try {
      await context.queryClient.ensureQueryData(meQuery)
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        throw redirect({ to: '/login', search: { redirect: location.href } })
      }
      throw e
    }
  },
  component: AppLayout,
})

function AppLayout() {
  return (
    <div className="grid h-svh grid-cols-[16rem_1fr]">
      <Sidebar />
      <main className="overflow-y-auto px-12 py-10">
        <Outlet />
      </main>
    </div>
  )
}
