// Historia: the newest 20 Versions (first page); a picked Version renders read-only
import { Link } from '@tanstack/react-router'
import { useVersions } from '@/api/hooks'
import type { Page, VersionKind } from '@/api/types'
import { PageView } from '@/components/PageView'
import { pageSplat, parsePage } from '@/wiki'

const KIND_LABELS: Record<VersionKind, string> = {
  created: 'Created',
  generation: 'Generation',
  proposal: 'Proposal',
  edit: 'Edit',
}

const when = (iso: string) =>
  new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })

export function PageHistory({ page, versionId }: { page: Page; versionId?: number }) {
  const { data } = useVersions(page.path)
  if (!data) return null
  const versions = data.data
  const params = { _splat: pageSplat(page.path) }
  // Oldest is v1; only the newest 20 are loaded, so number from the server total
  const label = (i: number) => `v${data.total - i}`

  if (versionId !== undefined) {
    const i = versions.findIndex((v) => v.id === versionId)
    if (i === -1) {
      return (
        <p className="text-muted-foreground">
          Version not found.{' '}
          <Link to="/$" params={params} search={{ view: 'history' }} className="text-primary">
            History
          </Link>
        </p>
      )
    }
    const version = versions[i]
    const title = parsePage(version.content).frontmatter.title ?? page.title
    return (
      <article>
        <p className="mb-6 flex flex-wrap gap-3 rounded-md border bg-muted px-4 py-2 text-sm">
          <span className="font-semibold">
            Viewing {label(i)} · {KIND_LABELS[version.kind]} · {when(version.created_at)}
          </span>
          <Link to="/$" params={params} search={{ view: 'history' }} className="text-primary">
            History
          </Link>
          <Link to="/$" params={params} search={{}} className="text-primary">
            Back to current
          </Link>
        </p>
        <PageView page={{ ...page, content: version.content, title }} />
      </article>
    )
  }

  return (
    <section>
      <Link
        to="/$"
        params={params}
        search={{}}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← {page.title}
      </Link>
      <h1 className="mt-2 font-heading text-3xl">History</h1>
      <ol aria-label="Versions" className="mt-6 divide-y rounded-md border">
        {versions.map((v, i) => (
          <li key={v.id} className="flex items-center gap-3 px-4 py-3 text-sm">
            <span className="font-mono text-muted-foreground">{label(i)}</span>
            <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold">
              {KIND_LABELS[v.kind]}
            </span>
            <span className="text-muted-foreground">
              {v.author} · {when(v.created_at)}
            </span>
            <Link
              to="/$"
              params={params}
              search={{ view: 'history', v: v.id }}
              className="ml-auto text-primary"
            >
              View
            </Link>
          </li>
        ))}
      </ol>
      <p className="mt-3 text-sm text-muted-foreground">
        Rejected proposals don&apos;t create versions.
      </p>
    </section>
  )
}
