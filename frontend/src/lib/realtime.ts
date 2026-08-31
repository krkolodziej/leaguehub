import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import type { Match, MatchEvent } from './api'

export type LiveMatchStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected'

type LiveMessage = {
  type?: string
  match?: Match
  event?: MatchEvent
}

export function useLiveMatch(organizationId: number | undefined, leagueId: number | undefined, seasonId: number | undefined, matchId: number | undefined): LiveMatchStatus {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<LiveMatchStatus>('disconnected')

  useEffect(() => {
    if (!organizationId || !leagueId || !seasonId || !matchId) {
      setStatus('disconnected')
      return
    }

    let stopped = false
    let attempts = 0
    let socket: WebSocket | undefined
    let reconnectTimer: number | undefined
    const matchKey = ['match', organizationId, leagueId, seasonId, matchId]
    const eventsKey = ['match-events', organizationId, leagueId, seasonId, matchId]
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const baseUrl = import.meta.env.VITE_WS_BASE_URL ?? `${protocol}//${window.location.host}`
    const url = `${baseUrl}/ws/organizations/${organizationId}/leagues/${leagueId}/seasons/${seasonId}/matches/${matchId}/`

    const connect = () => {
      if (stopped) return
      setStatus(attempts === 0 ? 'connecting' : 'reconnecting')
      socket = new WebSocket(url)
      socket.onopen = () => {
        attempts = 0
        setStatus('connected')
      }
      socket.onmessage = (message) => {
        try {
          const payload = JSON.parse(message.data) as LiveMessage
          if (payload.match) queryClient.setQueryData<Match>(matchKey, payload.match)
          if (payload.event) {
            queryClient.setQueryData<MatchEvent[]>(eventsKey, (current = []) => current.some((event) => event.id === payload.event?.id) ? current : [...current, payload.event!])
          }
        } catch {
          // Ignore malformed messages; the next snapshot will restore the cache.
        }
      }
      socket.onclose = () => {
        if (stopped) return
        setStatus('reconnecting')
        const delay = Math.min(1000 * 2 ** attempts, 10000)
        attempts += 1
        reconnectTimer = window.setTimeout(connect, delay)
      }
      socket.onerror = () => socket?.close()
    }

    connect()
    return () => {
      stopped = true
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [organizationId, leagueId, seasonId, matchId, queryClient])

  return status
}
