import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ErrorState } from './ErrorState'

describe('ErrorState', () => {
  it('shows the error and calls retry when requested', async () => {
    const user = userEvent.setup()
    const retry = vi.fn()
    render(<ErrorState error={new Error('The API is unavailable.')} retry={retry} />)

    expect(screen.getByRole('alert')).toHaveTextContent('The API is unavailable.')
    await user.click(screen.getByRole('button', { name: 'Try again' }))
    expect(retry).toHaveBeenCalledOnce()
  })
})
