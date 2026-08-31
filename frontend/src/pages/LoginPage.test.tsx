import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../lib/api'
import { LoginPage } from './LoginPage'

const login = vi.hoisted(() => vi.fn())

vi.mock('../lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../lib/api')>()),
  login,
}))

function renderPage() {
  const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/login']}>
        <LoginPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => {
  // Vitest runs without globals, so Testing Library cannot auto-clean the DOM.
  cleanup()
  login.mockReset()
})

describe('LoginPage', () => {
  it('signs in with the demo account in a single click', async () => {
    const user = userEvent.setup()
    login.mockResolvedValue({ id: 1, email: 'demo@leaguehub.app', first_name: '', last_name: '' })
    renderPage()

    expect(screen.getByText('demo@leaguehub.app')).toBeVisible()
    expect(screen.getByText('demo1234')).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Sign in to the demo' }))

    expect(login).toHaveBeenCalledWith({ email: 'demo@leaguehub.app', password: 'demo1234' })
    // The visitor can see which credentials were used.
    expect(screen.getByLabelText('Email')).toHaveValue('demo@leaguehub.app')
  })

  it('reports a rejected sign-in in plain words', async () => {
    const user = userEvent.setup()
    login.mockRejectedValue(
      new ApiError(400, { detail: 'Invalid email or password.', code: 'invalid_credentials' }),
    )
    renderPage()

    await user.type(screen.getByLabelText('Email'), 'someone@leaguehub.app')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect.')
  })

  it('places validation errors on the field they belong to', async () => {
    const user = userEvent.setup()
    login.mockRejectedValue(
      new ApiError(400, {
        detail: 'Request validation failed.',
        code: 'validation_error',
        fields: { email: ['Enter a valid email address.'] },
      }),
    )
    renderPage()

    await user.type(screen.getByLabelText('Email'), 'not-an-email@example')
    await user.type(screen.getByLabelText('Password'), 'some-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Enter a valid email address.')).toBeVisible()
    expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
