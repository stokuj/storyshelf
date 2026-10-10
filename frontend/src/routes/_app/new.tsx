// New page: pick a Type, fill the Template fields, create an empty Page (no Agent)
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { apiErrorMessage } from '@/api/client'
import { useCreatePage, usePages } from '@/api/hooks'
import type { NewPage, PageType } from '@/api/types'
import { pageSplat, previewPath } from '@/wiki'

export const Route = createFileRoute('/_app/new')({
  component: NewPageForm,
})

const TYPES: [PageType, string][] = [
  ['book', 'Book'],
  ['character', 'Character'],
  ['place', 'Place'],
  ['universe', 'Universe'],
]

const field = 'flex flex-col gap-1.5 text-sm font-semibold'
const control = 'rounded-md border bg-background px-3 py-1.5 font-normal'
const optional = <span className="text-xs font-normal text-muted-foreground">optional</span>

function NewPageForm() {
  const [type, setType] = useState<PageType>('book')
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [year, setYear] = useState('')
  const [universe, setUniverse] = useState('')
  const [book, setBook] = useState('')
  const pages = usePages().data ?? []
  const books = pages.filter((p) => p.type === 'book')
  const universes = pages.filter((p) => p.type === 'universe')
  const create = useCreatePage()
  const navigate = useNavigate()
  // isPending updates after re-render, so a fast double click would start a second create
  const started = useRef(false)
  const needsBook = type === 'character' || type === 'place'
  const ready = title.trim() !== '' && (!needsBook || book !== '')
  const preview = previewPath(type, title, book)

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!ready || started.current) return
    started.current = true
    // undefined fields are dropped by JSON.stringify, so only the chosen Type's fields are sent
    const input: NewPage = {
      type,
      title: title.trim(),
      author: type === 'book' ? author.trim() || undefined : undefined,
      year: type === 'book' && year ? Number(year) : undefined,
      universe: type === 'book' ? universe || undefined : undefined,
      book: needsBook ? book : undefined,
    }
    create.mutate(input, {
      onSuccess: (page) => navigate({ to: '/$', params: { _splat: pageSplat(page.path) } }),
      onError: () => (started.current = false),
    })
  }

  return (
    <section className="max-w-xl">
      <h1 className="font-heading text-3xl">New page</h1>
      <p className="mt-1 text-muted-foreground">
        Start an empty page from a template. You fill it in yourself.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-4 rounded-lg border p-6">
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-2 text-sm font-semibold">Type</legend>
          <div className="grid grid-cols-4 gap-1.5 rounded-md bg-muted p-1">
            {TYPES.map(([value, label]) => (
              <label
                key={value}
                className="rounded-md py-1.5 text-center text-sm has-checked:bg-background has-checked:font-semibold has-checked:text-primary has-focus-visible:ring-2 has-focus-visible:ring-ring"
              >
                <input
                  type="radio"
                  name="type"
                  checked={type === value}
                  onChange={() => setType(value)}
                  className="sr-only"
                />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <label className={field}>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} className={control} />
        </label>

        {type === 'book' && (
          <>
            <div className="grid grid-cols-[2fr_1fr] gap-3">
              <label className={field}>
                Author {optional}
                <input
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  className={control}
                />
              </label>
              <label className={field}>
                Year {optional}
                <input
                  type="number"
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className={control}
                />
              </label>
            </div>
            <label className={field}>
              Universe {optional}
              <select
                value={universe}
                onChange={(e) => setUniverse(e.target.value)}
                className={control}
              >
                <option value="">None</option>
                {universes.map((u) => (
                  <option key={u.path} value={u.path}>
                    {u.title}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}

        {needsBook && (
          <label className={field}>
            Book
            <select
              value={book}
              onChange={(e) => setBook(e.target.value)}
              disabled={books.length === 0}
              className={control}
            >
              <option value="">{books.length ? 'Choose a book…' : 'Add a book first'}</option>
              {books.map((b) => (
                <option key={b.path} value={b.path}>
                  {b.title}
                </option>
              ))}
            </select>
          </label>
        )}

        {preview && (
          <p className="text-sm text-muted-foreground">
            Path: <code>{preview}</code>
          </p>
        )}

        {create.error && (
          <p
            role="alert"
            className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {apiErrorMessage(create.error)}
          </p>
        )}

        <button
          type="submit"
          disabled={!ready || create.isPending}
          className="w-fit rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
        >
          Create page
        </button>
      </form>
    </section>
  )
}
