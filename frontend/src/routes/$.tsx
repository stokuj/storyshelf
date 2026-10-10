import { Link, createFileRoute } from '@tanstack/react-router'
import { useEffect } from 'react'
import { useGeneratePage, usePage, usePages, useProposals } from '@/api/hooks'
import type { Page } from '@/api/types'
import { PageEditor } from '@/components/PageEditor'
import { PageHistory } from '@/components/PageHistory'
import { PageView } from '@/components/PageView'
import { ProposalView } from '@/components/ProposalView'
import { pagePath, pageSplat, parsePage, universeMembers } from '@/wiki'

const VIEWS = ['edit', 'history', 'proposal'] as const
type PageSearch = { view?: (typeof VIEWS)[number]; v?: number; p?: number }

// A present but non-numeric id (?v=abc) maps to an id that never exists → "not found"
const searchId = (x: unknown) => (x === undefined ? undefined : typeof x === 'number' ? x : -1)

export const Route = createFileRoute('/$')({
  // Unknown values are dropped, so a bad ?view= falls back to the page itself
  validateSearch: (s: Record<string, unknown>): PageSearch => ({
    view: VIEWS.find((x) => x === s.view),
    v: searchId(s.v),
    p: searchId(s.p),
  }),
  component: PageRoute,
})

function PageRoute() {
  const { _splat = '' } = Route.useParams()
  const { view, v, p } = Route.useSearch()
  const { data: page, isError } = usePage(pagePath(_splat))
  useEffect(() => {
    document.title = page ? `${page.title} · StoryShelf` : 'StoryShelf'
    return () => {
      document.title = 'StoryShelf'
    }
  }, [page])
  if (isError) {
    return (
      <p className="text-muted-foreground">
        Page not found.{' '}
        <Link to="/" className="text-primary">
          Home
        </Link>
      </p>
    )
  }
  if (!page) return null

  if (view === 'edit') return <PageEditor key={page.path} page={page} />
  if (view === 'history') return <PageHistory page={page} versionId={v} />
  if (view === 'proposal' && p !== undefined) return <ProposalView page={page} proposalId={p} />

  return (
    <article>
      <PageActions page={page} />
      <GenerateCard key={page.path} page={page} />
      <OpenProposals page={page} />
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

// Generowanie: the Agent fills an empty (draft) book once; later changes come as Proposals
function GenerateCard({ page }: { page: Page }) {
  const generate = useGeneratePage(page.path)
  if (page.type !== 'book' || parsePage(page.content).frontmatter.status !== 'draft') return null
  return (
    <section className="mb-6 rounded-md border bg-muted p-4">
      <h2 className="font-heading text-xl">This page is empty</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The Agent writes the summary, characters and places. The first generation is saved directly;
        later changes come as proposals.
      </p>
      <button
        type="button"
        disabled={generate.isPending}
        onClick={() => generate.mutate()}
        className="mt-3 rounded-md bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
      >
        {generate.isPending ? 'Generating…' : 'Generate with Agent'}
      </button>
      {generate.error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {generate.error.message}
        </p>
      )}
    </section>
  )
}

function OpenProposals({ page }: { page: Page }) {
  const { data: proposals = [] } = useProposals(page.path)
  const pending = proposals.filter((p) => p.status === 'open' || p.status === 'stale')
  if (pending.length === 0) return null
  return (
    <ul className="mb-6 space-y-2">
      {pending.map((p) => (
        <li key={p.id} className="rounded-md border bg-muted px-4 py-2 text-sm">
          Proposal: {p.prompt}{' '}
          <Link
            to="/$"
            params={{ _splat: pageSplat(page.path) }}
            search={{ view: 'proposal', p: p.id }}
            className="font-semibold text-primary"
          >
            Review
          </Link>
        </li>
      ))}
    </ul>
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
