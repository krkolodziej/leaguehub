import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from './api'
import { authQueryKey, useLogout } from './auth'

const logout = vi.hoisted(() => vi.fn())

vi.mock('./api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./api')>()),
  logout,
}))

function wrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

afterEach(() => logout.mockReset())

describe('useLogout', () => {
  it('clears the signed-in user on success', async () => {
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
    client.setQueryData(authQueryKey, { id: 1, email: 'a@b.c', first_name: '', last_name: '' })
    logout.mockResolvedValue(undefined)

    const { result } = renderHook(() => useLogout(), { wrapper: wrapper(client) })
    await act(async () => void result.current.mutate())

    await waitFor(() => expect(client.getQueryData(authQueryKey)).toBeNull())
  })

  it('still signs the viewer out when the session has already expired', async () => {
    // The server answering 401 means the session is gone. Treating that as a
    // failure left the button doing nothing at all, stranding the viewer.
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
    client.setQueryData(authQueryKey, { id: 1, email: 'a@b.c', first_name: '', last_name: '' })
    logout.mockRejectedValue(new ApiError(401, { detail: 'Not authenticated.' }))

    const { result } = renderHook(() => useLogout(), { wrapper: wrapper(client) })
    await act(async () => void result.current.mutate())

    await waitFor(() => expect(client.getQueryData(authQueryKey)).toBeNull())
    expect(result.current.isError).toBe(false)
  })

  it('treats a permission-denied logout as an expired session too', async () => {
    // With HTTP Basic removed, DRF reports "not authenticated" as 403.
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
    client.setQueryData(authQueryKey, { id: 1, email: 'a@b.c', first_name: '', last_name: '' })
    logout.mockRejectedValue(
      new ApiError(403, { detail: 'Not authenticated.', code: 'permission_denied' }),
    )

    const { result } = renderHook(() => useLogout(), { wrapper: wrapper(client) })
    await act(async () => void result.current.mutate())

    await waitFor(() => expect(client.getQueryData(authQueryKey)).toBeNull())
    expect(result.current.isError).toBe(false)
  })

  it('reports a genuine failure instead of pretending to sign out', async () => {
    // A CSRF rejection comes from Django as HTML, so it carries no code.
    const client = new QueryClient({ defaultOptions: { mutations: { retry: false } } })
    const user = { id: 1, email: 'a@b.c', first_name: '', last_name: '' }
    client.setQueryData(authQueryKey, user)
    logout.mockRejectedValue(new ApiError(403, { detail: 'CSRF verification failed.' }))

    const { result } = renderHook(() => useLogout(), { wrapper: wrapper(client) })
    await act(async () => void result.current.mutate())

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(client.getQueryData(authQueryKey)).toEqual(user)
  })
})
