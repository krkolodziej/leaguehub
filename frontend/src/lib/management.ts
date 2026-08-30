import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  addRosterEntry,
  addSeasonTeam,
  createLeague,
  createOrganization,
  createPlayer,
  createSeason,
  createTeam,
  getLeagues,
  getPlayers,
  getRoster,
  getSeasonTeams,
  getSeasons,
  getTeams,
} from './api'

export function useLeagues(organizationId: number | undefined) {
  return useQuery({ queryKey: ['leagues', organizationId], queryFn: () => getLeagues(organizationId!), enabled: Boolean(organizationId), retry: false })
}
export function useTeams(organizationId: number | undefined) {
  return useQuery({ queryKey: ['teams', organizationId], queryFn: () => getTeams(organizationId!), enabled: Boolean(organizationId), retry: false })
}
export function usePlayers(organizationId: number | undefined) {
  return useQuery({ queryKey: ['players', organizationId], queryFn: () => getPlayers(organizationId!), enabled: Boolean(organizationId), retry: false })
}
export function useSeasons(organizationId: number | undefined, leagueId: number | undefined) {
  return useQuery({ queryKey: ['seasons', organizationId, leagueId], queryFn: () => getSeasons(organizationId!, leagueId!), enabled: Boolean(organizationId && leagueId), retry: false })
}
export function useSeasonTeams(organizationId: number | undefined, leagueId: number | undefined, seasonId: number | undefined) {
  return useQuery({ queryKey: ['season-teams', organizationId, leagueId, seasonId], queryFn: () => getSeasonTeams(organizationId!, leagueId!, seasonId!), enabled: Boolean(organizationId && leagueId && seasonId), retry: false })
}
export function useRoster(organizationId: number | undefined, leagueId: number | undefined, seasonId: number | undefined, seasonTeamId: number | undefined) {
  return useQuery({ queryKey: ['roster', organizationId, leagueId, seasonId, seasonTeamId], queryFn: () => getRoster(organizationId!, leagueId!, seasonId!, seasonTeamId!), enabled: Boolean(organizationId && leagueId && seasonId && seasonTeamId), retry: false })
}

function invalidate(client: ReturnType<typeof useQueryClient>, keys: unknown[][]) {
  keys.forEach((queryKey) => void client.invalidateQueries({ queryKey }))
}

export function useCreateOrganization() {
  const client = useQueryClient()
  return useMutation({ mutationFn: createOrganization, onSuccess: () => invalidate(client, [['organizations']]) })
}
export function useCreateLeague(organizationId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (body: { name: string; slug: string; description: string }) => createLeague(organizationId, body), onSuccess: () => invalidate(client, [['leagues', organizationId]]) })
}
export function useCreateSeason(organizationId: number, leagueId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (body: { name: string; start_date: string; end_date?: string }) => createSeason(organizationId, leagueId, body), onSuccess: () => invalidate(client, [['seasons', organizationId, leagueId]]) })
}
export function useCreateTeam(organizationId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (body: { name: string; slug: string }) => createTeam(organizationId, body), onSuccess: () => invalidate(client, [['teams', organizationId]]) })
}
export function useCreatePlayer(organizationId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (body: { first_name: string; last_name: string; date_of_birth?: string }) => createPlayer(organizationId, body), onSuccess: () => invalidate(client, [['players', organizationId]]) })
}
export function useAddSeasonTeam(organizationId: number, leagueId: number, seasonId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (teamId: number) => addSeasonTeam(organizationId, leagueId, seasonId, teamId), onSuccess: () => invalidate(client, [['season-teams', organizationId, leagueId, seasonId]]) })
}
export function useAddRosterEntry(organizationId: number, leagueId: number, seasonId: number, seasonTeamId: number) {
  const client = useQueryClient()
  return useMutation({ mutationFn: (body: { player_id: number; shirt_number?: number; position?: string; is_captain?: boolean }) => addRosterEntry(organizationId, leagueId, seasonId, seasonTeamId, body), onSuccess: () => invalidate(client, [['roster', organizationId, leagueId, seasonId, seasonTeamId]]) })
}
