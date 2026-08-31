import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getNotifications, markNotificationRead } from './api'

export function useNotifications() {
  return useQuery({ queryKey: ['notifications'], queryFn: getNotifications, retry: false })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })
}
