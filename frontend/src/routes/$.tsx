import { Link, createFileRoute } from '@tanstack/react-router'
import { usePage, usePages } from '@/api/hooks'
import type { Page } from '@/api/types'
import { PageEditor } from '@/components/PageEditor'
import { PageHistory } from '@/components/PageHistory'
import { PageView } from '@/components/PageView'
import { pagePath, pageSplat, universeMembers } from '@/wiki'

const VIEWS = ['edit', 'history', 'proposal'] as const
type PageSearch = { view?: (typeof VIEWS)[number]; v?: number; p?: number }

export const Route = createFileRoute('/$')({
  // Unknown values are dropped, so a bad ?view= falls back to the page itself
  validateSearch: (s: Record<string, unknown>): PageSearch => ({
    view: VIEWS.find((x) => x === s.view),
    v: typeof s.v === 'number' ? s.v : undefined,
    p: typeof s.p === 'number' ? s.p : undefined,
  }),
  component: PageRoute,
})

function PageRoute() {
  const { _splat = '' } = Route.useParams()
  const { view, v } = Route.useSearch()
  const { data: page, isError } = usePage(pagePath(_splat))
  if (isError) return <p className="text-muted-foreground">Page not found.</p>
  if (!page) return null

  if (view === 'edit') return <PageEditor key={page.path} page={page} />
  if (view === 'history') return <PageHistory page={page} versionId={v} />

  return (
    <article>
      <PageActions page={page} />
      <PageView page={page}>
        {page.type === 'universe' && <UniverseMembers universe={page.path} />}
      </PageView>
    </article>
  )
}

function PageActions({ page }: { page: Page }) {
  const params = { _splat: pageSplat(page.path) }
  return (
    <nav aria-label="Page actions" className="mb-6 flex gap-4 text-sm">
      <Link to="/$" params={params} search={{ view: 'edit' }} className="hover:text-primary">
        Edit
      </Link>
      <Link to="/$" params={params} search={{ view: 'history' }} className="hover:text-primary">
        History
      </Link>
    </nav>
  )
}

function UniverseMembers({ universe }: { universe: string }) {
  const { data: pages = [] } = usePages()
  const { books, characters, places } = universeMembers(pages, universe)
  const titles = new Map(pages.map((p) => [p.path, p.title]))
  return (
    <>
      <PageList title="Books in this universe" pages={books} titles={titles} />
      <PageList title="Characters in this universe" pages={characters} titles={titles} />
      <PageList title="Places in this universe" pages={places} titles={titles} />
    </>
  )
}

function PageList({
  title,
  pages,
  titles,
}: {
  title: string
  pages: Page[]
  titles: Map<string, string>
}) {
  if (pages.length === 0) return null
  return (
    <section className="mt-8">
      <h2 className="font-heading text-xl">{title}</h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {pages.map((p) => (
          <li key={p.path}>
            <Link
              to="/$"
              params={{ _splat: pageSplat(p.path) }}
              className="block rounded-md border px-3 py-1 text-sm hover:text-primary"
            >
              {p.title}
              {p.book && (
                <span className="ml-2 text-muted-foreground">{titles.get(p.book) ?? p.book}</span>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
