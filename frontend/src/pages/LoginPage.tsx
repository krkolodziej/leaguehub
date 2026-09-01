import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { FormField } from '../components/FormField'
import { Button } from '../components/ui/button'
import { getDemoAccount } from '../lib/demo'
import { errorMessage, fieldErrors } from '../lib/errors'
import { useLogin } from '../lib/auth'

const demo = getDemoAccount()

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const loginMutation = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const destination = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const fields = fieldErrors(loginMutation.error)
  const formError = loginMutation.isError && Object.keys(fields).length === 0
    ? errorMessage(loginMutation.error)
    : fields.non_field_errors

  const signIn = (credentials: { email: string; password: string }) => {
    loginMutation.mutate(credentials, { onSuccess: () => navigate(destination, { replace: true }) })
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    signIn({ email, password })
  }

  const handleDemoSignIn = () => {
    if (!demo) return
    setEmail(demo.email)
    setPassword(demo.password)
    signIn(demo)
  }

  return (
    <>
      <h1 className="mt-6 text-xl">Sign in to LeagueHub</h1>
      <p className="mt-1 text-sm text-ink-muted">Manage your leagues, fixtures and results.</p>
      {formError && (
        <p className="mt-4 border-l-[3px] border-ink bg-paper px-3 py-2 text-sm font-medium text-ink" role="alert">
          {formError}
        </p>
      )}
      <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
        <FormField
          id="email"
          label="Email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          error={fields.email}
          required
          autoComplete="email"
          autoFocus
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          error={fields.password}
          required
          autoComplete="current-password"
        />
        <Button className="mt-1 w-full" size="lg" disabled={loginMutation.isPending} type="submit">
          {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      {demo && (
        <section className="mt-7 border-t border-chalk pt-5" aria-labelledby="demo-heading">
          <h2 id="demo-heading" className="text-base">
            Just looking around?
          </h2>
          <p className="mt-1 text-sm text-ink-muted">
            Sign in to a populated league with the shared demo account.
          </p>
          <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 rounded-[var(--radius-control)] border border-chalk bg-paper px-3 py-2.5 text-sm">
            <dt className="text-ink-muted">Email</dt>
            <dd className="m-0 select-all font-condensed font-semibold">{demo.email}</dd>
            <dt className="text-ink-muted">Password</dt>
            <dd className="m-0 select-all font-condensed font-semibold">{demo.password}</dd>
          </dl>
          <Button
            className="mt-3 w-full"
            variant="outline"
            size="lg"
            disabled={loginMutation.isPending}
            onClick={handleDemoSignIn}
            type="button"
          >
            Sign in to the demo
          </Button>
        </section>
      )}
      <p className="mt-6 text-center text-sm text-ink-muted">
        New to LeagueHub?{' '}
        <Link className="font-semibold text-pitch underline-offset-4 hover:underline" to="/register">
          Create an account
        </Link>
      </p>
    </>
  )
}
