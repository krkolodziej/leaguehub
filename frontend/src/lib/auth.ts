import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  ApiError,
  getCurrentUser,
  login,
  logout,
  register,
  type LoginInput,
  type RegisterInput,
  type User,
} from './api'

export const authQueryKey = ['auth', 'current-user'] as const

/**
 * DRF answers an unauthenticated request with 401 when an authentication
 * scheme advertises a challenge, and with 403 when none does. Either way the
 * session is gone. A CSRF rejection is also a 403, but Django serves that one
 * as HTML, so it arrives without the API's `code` field and stays an error.
 */
function isAlreadySignedOut(error: unknown): boolean {
  if (!(error instanceof ApiError)) return false
  if (error.status === 401) return true
  return error.status === 403 && error.code === 'permission_denied'
}

export function useCurrentUser() {
  return useQuery<User, ApiError>({
    queryKey: authQueryKey,
    queryFn: getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: LoginInput) => login(input),
    onSuccess: (user) => queryClient.setQueryData(authQueryKey, user),
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: RegisterInput) => register(input),
    onSuccess: (user) => queryClient.setQueryData(authQueryKey, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      try {
        await logout()
      } catch (error) {
        // A session the server has already dropped means the work is done.
        // Without this the button silently does nothing and the viewer is
        // stranded on a page they are no longer authenticated for.
        if (isAlreadySignedOut(error)) return
        throw error
      }
    },
    onSuccess: () => {
      queryClient.setQueryData(authQueryKey, null)
      queryClient.removeQueries({ queryKey: ['organizations'] })
    },
  })
}
