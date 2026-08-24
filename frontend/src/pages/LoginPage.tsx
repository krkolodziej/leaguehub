import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { errorMessage } from '../lib/errors'
import { useLogin } from '../lib/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const loginMutation = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const destination = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    loginMutation.mutate({ email, password }, { onSuccess: () => navigate(destination, { replace: true }) })
  }

  return (
    <div className="auth-card">
      <p className="eyebrow">Welcome back</p>
      <h2>Sign in to LeagueHub</h2>
      <p className="muted">Use your account to manage your leagues.</p>
      {loginMutation.isError && <div className="form-error" role="alert">{errorMessage(loginMutation.error)}</div>}
      <form className="form-stack" onSubmit={handleSubmit}>
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label>
        <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label>
        <button className="button button-primary button-wide" disabled={loginMutation.isPending} type="submit">
          {loginMutation.isPending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className="auth-switch">New to LeagueHub? <Link to="/register">Create an account</Link></p>
    </div>
  )
}
