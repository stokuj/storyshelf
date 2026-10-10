import type { InputHTMLAttributes, ReactNode } from 'react'

export function AuthCard({
  title,
  error,
  children,
}: {
  title: string
  error?: string
  children: ReactNode
}) {
  return (
    <main className="grid min-h-svh place-items-center bg-sidebar px-4">
      <section className="w-full max-w-sm rounded-lg border bg-background p-8">
        <p className="font-heading text-xl font-semibold">StoryShelf</p>
        <h1 className="mt-6 font-heading text-3xl">{title}</h1>
        {error && (
          <p role="alert" className="mt-4 text-sm text-destructive">
            {error}
          </p>
        )}
        {children}
      </section>
    </main>
  )
}

export function Field({
  label,
  error,
  hint,
  ...input
}: { label: string; error?: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="mt-4 block text-sm font-medium">
      {label}
      <input
        required
        {...input}
        className="mt-1 block w-full rounded-md border bg-background px-3 py-2 font-normal"
      />
      {(error ?? hint) && (
        <span
          className={`mt-1 block text-xs ${error ? 'text-destructive' : 'text-muted-foreground'}`}
        >
          {error ?? hint}
        </span>
      )}
    </label>
  )
}

export function SubmitButton({ pending, children }: { pending: boolean; children: ReactNode }) {
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-6 w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
    >
      {children}
    </button>
  )
}
