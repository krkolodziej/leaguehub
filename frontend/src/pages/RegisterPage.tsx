import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { FormField } from '../components/FormField'
import { errorMessage, fieldErrors } from '../lib/errors'
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

  const fields = fieldErrors(registerMutation.error)
  const formError = registerMutation.isError && Object.keys(fields).length === 0
    ? errorMessage(registerMutation.error)
    : fields.non_field_errors

  return (
    <>
      <h1>Create your account</h1>
      <p className="muted">Set up a workspace for your league.</p>
      {formError && <div className="form-error" role="alert">{formError}</div>}
      <form className="form-stack" onSubmit={handleSubmit}>
        <div className="form-row">
          <FormField
            id="first-name"
            label="First name"
            value={form.first_name}
            onChange={update('first_name')}
            error={fields.first_name}
            autoComplete="given-name"
            autoFocus
          />
          <FormField
            id="last-name"
            label="Last name"
            value={form.last_name}
            onChange={update('last_name')}
            error={fields.last_name}
            autoComplete="family-name"
          />
        </div>
        <FormField
          id="email"
          label="Email"
          type="email"
          value={form.email}
          onChange={update('email')}
          error={fields.email}
          required
          autoComplete="email"
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          value={form.password}
          onChange={update('password')}
          error={fields.password}
          hint="At least 8 characters."
          required
          minLength={8}
          autoComplete="new-password"
        />
        <FormField
          id="password-confirm"
          label="Confirm password"
          type="password"
          value={form.password_confirm}
          onChange={update('password_confirm')}
          error={fields.password_confirm}
          required
          minLength={8}
          autoComplete="new-password"
        />
        <button className="button button-primary button-wide" disabled={registerMutation.isPending} type="submit">
          {registerMutation.isPending ? 'Creating account…' : 'Create account'}
        </button>
      </form>
      <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
    </>
  )
}
