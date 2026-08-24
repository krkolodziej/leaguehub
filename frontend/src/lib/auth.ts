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
    mutationFn: logout,
    onSuccess: () => {
      queryClient.setQueryData(authQueryKey, null)
      queryClient.removeQueries({ queryKey: ['organizations'] })
    },
  })
}
