import { Link, createFileRoute } from '@tanstack/react-router'
import { usePage, usePages } from '@/api/hooks'
import type { Page } from '@/api/types'
import { PageView } from '@/components/PageView'
import { pagePath, pageSplat, universeMembers } from '@/wiki'

export const Route = createFileRoute('/$')({
  component: PageRoute,
})

function PageRoute() {
  const { _splat = '' } = Route.useParams()
  const { data: page, isError } = usePage(pagePath(_splat))
  if (isError) return <p className="text-muted-foreground">Page not found.</p>
  if (!page) return null

  return (
    <article>
      <PageView page={page}>
        {page.type === 'universe' && <UniverseMembers universe={page.path} />}
      </PageView>
    </article>
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
