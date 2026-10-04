import { Outlet, createRootRoute } from '@tanstack/react-router'
import { Sidebar } from '@/components/Sidebar'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <div className="grid h-svh grid-cols-[16rem_1fr]">
      <Sidebar />
      <main className="overflow-y-auto px-12 py-10">
        <Outlet />
      </main>
    </div>
  )
}
