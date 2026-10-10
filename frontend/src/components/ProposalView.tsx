// Propozycja: line diff against its base Version; accept/reject, accept blocked when stale
import { Link, useNavigate } from '@tanstack/react-router'
import { diffLines } from 'diff'
import { useAcceptProposal, useProposals, useRejectProposal, useVersions } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pageSplat } from '@/wiki'

const button = 'rounded-md px-4 py-1.5 text-sm font-semibold disabled:opacity-50'

export function ProposalView({ page, proposalId }: { page: Page; proposalId: number }) {
  const { data: proposals } = useProposals(page.path)
  const { data: versions } = useVersions(page.path)
  const accept = useAcceptProposal(page.path)
  const reject = useRejectProposal(page.path)
  const navigate = useNavigate()
  if (!proposals || !versions) return null

  const proposal = proposals.find((p) => p.id === proposalId)
  const params = { _splat: pageSplat(page.path) }
  if (!proposal) {
    return (
      <p className="text-muted-foreground">
        Proposal not found.{' '}
        <Link to="/$" params={params} search={{}} className="text-primary">
          Back to page
        </Link>
      </p>
    )
  }
  const base = versions.data.find((v) => v.id === proposal.base_version)
  const back = () => navigate({ to: '/$', params, search: {} })
  const error = accept.error ?? reject.error

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
      <h1 className="mt-2 font-heading text-3xl">Proposal from the Agent</h1>
      <div className="mt-6 rounded-md border bg-muted px-4 py-3">
        <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          You asked
        </p>
        <p className="mt-1">{proposal.prompt}</p>
      </div>

      <Diff before={base?.content ?? ''} after={proposal.content} />

      {error && (
        <p role="alert" className="mt-2 text-sm text-destructive">
          {error.message}
        </p>
      )}

      {proposal.status === 'open' && (
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            disabled={accept.isPending}
            onClick={() => accept.mutate(proposal.id, { onSuccess: back })}
            className={`${button} bg-primary text-primary-foreground`}
          >
            Accept → new version v{versions.total + 1}
          </button>
          <button
            type="button"
            disabled={reject.isPending}
            onClick={() => reject.mutate(proposal.id, { onSuccess: back })}
            className={`${button} border`}
          >
            Reject
          </button>
        </div>
      )}

      {proposal.status === 'stale' && (
        <div className="mt-4 space-y-2">
          <p className="text-sm">This page changed since the proposal was made.</p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled
              className={`${button} bg-primary text-primary-foreground`}
            >
              Accept → new version v{versions.total + 1}
            </button>
            <button type="button" disabled className={`${button} border`}>
              Regenerate
            </button>
            <span className="text-sm text-muted-foreground">Agent arrives in M3</span>
          </div>
        </div>
      )}

      {(proposal.status === 'accepted' || proposal.status === 'rejected') && (
        <p className="mt-4">
          <span className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold">
            {proposal.status}
          </span>
        </p>
      )}
    </section>
  )
}

function Diff({ before, after }: { before: string; after: string }) {
  const lines = diffLines(before, after).flatMap((part) =>
    part.value
      .replace(/\n$/, '')
      .split('\n')
      .map((text) => ({ text, added: part.added, removed: part.removed })),
  )
  return (
    <pre className="mt-6 overflow-x-auto rounded-md border p-3 font-mono text-sm whitespace-pre-wrap">
      {lines.map((l, i) => (
        <div
          key={i}
          className={
            l.added
              ? 'bg-green-50 text-green-900'
              : l.removed
                ? 'bg-red-50 text-red-900'
                : undefined
          }
        >
          {l.added ? '+ ' : l.removed ? '− ' : '  '}
          {l.text}
        </div>
      ))}
    </pre>
  )
}
