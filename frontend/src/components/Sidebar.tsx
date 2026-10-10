import { Link } from '@tanstack/react-router'
import { useLogout, useMe } from '@/api/auth'
import { usePages } from '@/api/hooks'
import type { PageType } from '@/api/types'
import { groupByType, pageSplat } from '@/wiki'

const SECTIONS: [PageType, string][] = [
  ['book', 'Books'],
  ['character', 'Characters'],
  ['place', 'Places'],
  ['universe', 'Universes'],
]

export function Sidebar() {
  const { data: pages = [] } = usePages()
  const { data: me } = useMe()
  const logout = useLogout()
  const groups = groupByType(pages)
  const titles = new Map(pages.map((p) => [p.path, p.title]))

  return (
    <nav aria-label="Wiki" className="flex flex-col gap-6 overflow-y-auto border-r bg-sidebar p-4">
      <Link
        to="/"
        activeOptions={{ exact: true }}
        className="px-2 font-heading text-xl font-semibold"
      >
        StoryShelf
      </Link>
      <Link
        to="/add"
        className="rounded-md border px-2 py-1 text-center text-sm font-semibold hover:bg-background"
        activeProps={{ className: 'bg-background text-primary' }}
      >
        Add book
      </Link>
      {SECTIONS.map(([type, label]) => (
        <section key={type}>
          <h2 className="mb-1 flex justify-between px-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
            {label} <span>{groups[type].length}</span>
          </h2>
          <ul>
            {groups[type].map((p) => (
              <li key={p.path}>
                <Link
                  to="/$"
                  params={{ _splat: pageSplat(p.path) }}
                  className="block rounded-md px-2 py-1 text-sm hover:bg-background"
                  activeProps={{ className: 'bg-background font-medium text-primary' }}
                >
                  {p.title}{' '}
                  {p.book && (
                    <span className="block text-xs font-normal text-muted-foreground">
                      {titles.get(p.book) ?? p.book}
                    </span>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
      {me && (
        <div className="mt-auto flex items-center justify-between gap-2">
          <Link
            to="/profile"
            className="rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-background"
            activeProps={{ className: 'bg-background font-medium text-primary' }}
          >
            @{me.handle}
          </Link>
          <button
            type="button"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            className="rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-background disabled:opacity-50"
          >
            Log out
          </button>
        </div>
      )}
    </nav>
  )
}
