// Add a book: chat with the Agent → Candidate cards → Page with an empty Szablon
import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import { useCreateBook, usePages, useFindCandidates } from '@/api/hooks'
import type { Candidate } from '@/api/types'
import { bookPath, pageSplat } from '@/wiki'

export const Route = createFileRoute('/add')({
  component: AddBookPage,
})

// One exchange; the chat lives in component state until the real Agent (M3)
interface Turn {
  prompt: string
  matched: boolean
  candidates: Candidate[]
  dismissed: boolean
}

const button = 'rounded-md px-4 py-1.5 text-sm font-semibold disabled:opacity-50'
const bubble = 'ml-auto w-fit rounded-md bg-muted px-3 py-2'

function AddBookPage() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const find = useFindCandidates()
  const input = useRef<HTMLInputElement>(null)
  const dismiss = (i: number) =>
    setTurns((ts) => ts.map((t, j) => (j === i ? { ...t, dismissed: true } : t)))

  return (
    <section className="max-w-2xl">
      <h1 className="font-heading text-3xl">Add a book</h1>
      <p className="mt-1 text-muted-foreground">
        Type a title, or just what you remember from the story.
      </p>

      <ol aria-label="Chat" aria-live="polite" className="mt-6 space-y-6">
        {turns.map((t, i) => (
          <li key={i} className="space-y-3">
            <p className={bubble}>{t.prompt}</p>
            <p>{t.matched ? 'Is it one of these?' : "I'm not sure. Maybe one of these?"}</p>
            {t.dismissed ? (
              <p>Try a different title or author.</p>
            ) : (
              <>
                {t.candidates.map((c) => (
                  <CandidateCard key={c.title} candidate={c} />
                ))}
                <button type="button" onClick={() => dismiss(i)} className={`${button} border`}>
                  None of these
                </button>
              </>
            )}
          </li>
        ))}
        {find.isPending && (
          <li className="space-y-3">
            <p className={bubble}>{find.variables}</p>
            <p className="text-muted-foreground">Thinking…</p>
          </li>
        )}
      </ol>

      <form
        className="mt-6 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          const prompt = draft.trim()
          if (!prompt || find.isPending) return
          find.mutate(prompt, {
            onSuccess: (r) => setTurns((ts) => [...ts, { prompt, ...r, dismissed: false }]),
          })
          setDraft('')
          input.current?.focus()
        }}
      >
        <input
          ref={input}
          aria-label="Message to Agent"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          className="flex-1 rounded-md border bg-background px-3 py-1.5"
        />
        <button
          type="submit"
          disabled={!draft.trim() || find.isPending}
          className={`${button} bg-primary text-primary-foreground`}
        >
          Send
        </button>
      </form>
    </section>
  )
}

function CandidateCard({ candidate: c }: { candidate: Candidate }) {
  const { data: pages = [] } = usePages()
  const create = useCreateBook()
  const navigate = useNavigate()
  // isPending updates after re-render, so a fast double click would start a second create
  const started = useRef(false)
  const path = bookPath(c.title)
  const exists = pages.some((p) => p.path === path)

  return (
    <article aria-label={c.title} className="flex items-center gap-4 rounded-md border p-3">
      <span aria-hidden className="h-16 w-11 shrink-0 rounded-sm bg-muted" />
      <div className="flex-1">
        <h2 className="font-heading text-lg">{c.title}</h2>
        <p className="text-sm text-muted-foreground">{`${c.author} · ${c.year}`}</p>
        {create.error && (
          <p role="alert" className="mt-1 text-sm text-destructive">
            {create.error.message}
          </p>
        )}
      </div>
      {exists ? (
        <Link
          to="/$"
          params={{ _splat: pageSplat(path) }}
          className="text-sm font-semibold text-primary"
        >
          Already in Wiki
        </Link>
      ) : (
        <button
          type="button"
          disabled={create.isPending}
          aria-label={`Yes, add ${c.title}`}
          onClick={() => {
            if (started.current) return
            started.current = true
            create.mutate(c, {
              onSuccess: (page) => navigate({ to: '/$', params: { _splat: pageSplat(page.path) } }),
              onError: () => (started.current = false),
            })
          }}
          className={`${button} bg-primary text-primary-foreground`}
        >
          Yes, add
        </button>
      )}
    </article>
  )
}
