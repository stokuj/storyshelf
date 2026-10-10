// Edycja: the raw .md in a textarea; the store validates it and records a Version
import { Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { ApiError, apiErrorMessage } from '@/api/client'
import { usePage, useSavePage } from '@/api/hooks'
import type { Page } from '@/api/types'
import { pageSplat } from '@/wiki'

export function PageEditor({ page }: { page: Page }) {
  const [content, setContent] = useState(page.content)
  const save = useSavePage(page.path)
  const { refetch } = usePage(page.path)
  const stale = save.error instanceof ApiError && save.error.status === 409
  // Pull the newest text from the server and start editing from it
  const reload = () =>
    refetch().then(({ data }) => {
      if (data) {
        setContent(data.content)
        save.reset()
      }
    })
  const navigate = useNavigate()
  const params = { _splat: pageSplat(page.path) }
  const back = () => navigate({ to: '/$', params, search: {} })

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        save.mutate({ content, baseVersion: page.version }, { onSuccess: back })
      }}
    >
      <Link
        to="/$"
        params={params}
        search={{}}
        className="text-sm text-muted-foreground hover:text-primary"
      >
        ← {page.title}
      </Link>
      <h1 className="mt-2 font-heading text-3xl">Edit</h1>
      <textarea
        aria-label="Page source"
        value={content}
        onChange={(e) => {
          setContent(e.target.value)
          if (save.error) save.reset() // the alert describes the old text
        }}
        rows={30}
        spellCheck={false}
        className="mt-4 w-full rounded-md border bg-background p-3 font-mono text-sm"
      />
      {save.error && (
        <div className="mt-2 flex items-center gap-3 text-sm">
          <p role="alert" className="text-destructive">
            {stale
              ? 'This page changed since you opened it. Reload to get the latest version.'
              : apiErrorMessage(save.error)}
          </p>
          {stale && (
            <button type="button" onClick={reload} className="rounded-md border px-3 py-1">
              Reload
            </button>
          )}
        </div>
      )}
      <div className="mt-4 flex gap-2">
        <button
          type="submit"
          disabled={save.isPending}
          className="rounded-md bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground"
        >
          Save
        </button>
        <button type="button" onClick={back} className="rounded-md border px-4 py-1.5 text-sm">
          Cancel
        </button>
      </div>
    </form>
  )
}
