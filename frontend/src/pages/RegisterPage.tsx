import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { errorMessage } from '../lib/errors'
import { useRegister } from '../lib/auth'

export function RegisterPage() {
  const navigate = useNavigate()
  const registerMutation = useRegister()
  const [form, setForm] = useState({ email: '', password: '', password_confirm: '', first_name: '', last_name: '' })
  const update = (field: keyof typeof form) => (event: ChangeEvent<HTMLInputElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }))
  }
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    registerMutation.mutate(form, { onSuccess: () => navigate('/dashboard', { replace: true }) })
  }

  return (
    <div className="auth-card">
      <p className="eyebrow">Get started</p>
      <h2>Create your account</h2>
      <p className="muted">Set up your LeagueHub workspace in seconds.</p>
      {registerMutation.isError && <div className="form-error" role="alert">{errorMessage(registerMutation.error)}</div>}
      <form className="form-stack" onSubmit={handleSubmit}>
        <div className="form-row"><label>First name<input value={form.first_name} onChange={update('first_name')} autoComplete="given-name" /></label><label>Last name<input value={form.last_name} onChange={update('last_name')} autoComplete="family-name" /></label></div>
        <label>Email<input type="email" value={form.email} onChange={update('email')} required autoComplete="email" /></label>
        <label>Password<input type="password" value={form.password} onChange={update('password')} required minLength={8} autoComplete="new-password" /></label>
        <label>Confirm password<input type="password" value={form.password_confirm} onChange={update('password_confirm')} required minLength={8} autoComplete="new-password" /></label>
        <button className="button button-primary button-wide" disabled={registerMutation.isPending} type="submit">
          {registerMutation.isPending ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
    </div>
  )
}
