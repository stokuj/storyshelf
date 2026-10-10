import { Link, createFileRoute, useNavigate } from '@tanstack/react-router'
import type { FormEvent } from 'react'
import { type Credentials, formErrors, useRegister } from '@/api/auth'
import { AuthCard, Field, SubmitButton } from '@/components/AuthCard'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const errors = formErrors(register.error)

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const data = Object.fromEntries(new FormData(e.currentTarget)) as unknown as Credentials & {
      handle: string
    }
    register.mutate(data, { onSuccess: () => navigate({ to: '/' }) })
  }

  return (
    <AuthCard title="Create account" error={errors.form}>
      <form onSubmit={submit}>
        <Field label="Email" name="email" type="email" autoComplete="email" error={errors.email} />
        {/* Same rule as RegisterSerializer.handle */}
        <Field
          label="Handle"
          name="handle"
          pattern="[a-z]{3,30}"
          autoComplete="username"
          hint="Lowercase letters, 3–30."
          error={errors.handle}
        />
        <Field
          label="Password"
          name="password"
          type="password"
          minLength={8}
          maxLength={72}
          autoComplete="new-password"
          error={errors.password}
        />
        <SubmitButton pending={register.isPending}>Create account</SubmitButton>
      </form>
      <Link to="/login" className="mt-4 block text-center text-sm text-primary">
        Have an account? Log in
      </Link>
    </AuthCard>
  )
}
