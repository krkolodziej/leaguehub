import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { FormField } from '../components/FormField'
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
      <h1>Sign in to LeagueHub</h1>
      <p className="muted">Manage your leagues, fixtures and results.</p>
      {formError && <div className="form-error" role="alert">{formError}</div>}
      <form className="form-stack" onSubmit={handleSubmit}>
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
        <button className="button button-primary button-wide" disabled={loginMutation.isPending} type="submit">
          {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      {demo && (
        <section className="demo-panel" aria-labelledby="demo-heading">
          <h2 id="demo-heading">Just looking around?</h2>
          <p>Sign in to a populated league with the shared demo account.</p>
          <dl className="demo-credentials">
            <dt>Email</dt>
            <dd>{demo.email}</dd>
            <dt>Password</dt>
            <dd>{demo.password}</dd>
          </dl>
          <button
            className="button button-secondary button-wide"
            disabled={loginMutation.isPending}
            onClick={handleDemoSignIn}
            type="button"
          >
            Sign in to the demo
          </button>
        </section>
      )}
      <p className="auth-switch">New to LeagueHub? <Link to="/register">Create an account</Link></p>
    </>
  )
}
