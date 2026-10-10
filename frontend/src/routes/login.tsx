import { Link, createFileRoute, useRouter } from '@tanstack/react-router'
import type { FormEvent } from 'react'
import { type Credentials, formErrors, safeRedirect, useLogin } from '@/api/auth'
import { AuthCard, Field, SubmitButton } from '@/components/AuthCard'

export const Route = createFileRoute('/login')({
  validateSearch: (s: Record<string, unknown>): { redirect?: string } => ({
    redirect: typeof s.redirect === 'string' ? s.redirect : undefined,
  }),
  component: LoginPage,
})

function LoginPage() {
  const { redirect } = Route.useSearch()
  const router = useRouter()
  const login = useLogin()
  const errors = formErrors(login.error)

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.currentTarget)) as unknown as Credentials
    // redirect is a full href (path + search), so push it as-is
    login.mutate(data, { onSuccess: () => router.history.push(safeRedirect(redirect)) })
  }

  return (
    <AuthCard title="Log in" error={errors.form}>
      <form onSubmit={submit}>
        <Field label="Email" name="email" type="email" autoComplete="email" error={errors.email} />
        <Field
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          error={errors.password}
        />
        <SubmitButton pending={login.isPending}>Log in</SubmitButton>
      </form>
      <Link to="/register" className="mt-4 block text-center text-sm text-primary">
        No account? Create one
      </Link>
    </AuthCard>
  )
}
