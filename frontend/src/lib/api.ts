export type ApiErrorShape = {
  detail?: string
  code?: string
  fields?: Record<string, unknown>
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly fields?: Record<string, unknown>

  constructor(status: number, body: ApiErrorShape) {
    super(body.detail ?? 'Something went wrong.')
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.fields = body.fields
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

function getCookie(name: string): string | undefined {
  const value = document.cookie
    .split('; ')
    .find((cookie) => cookie.startsWith(`${name}=`))
  return value ? decodeURIComponent(value.split('=').slice(1).join('=')) : undefined
}

async function ensureCsrfToken(): Promise<void> {
  if (getCookie('csrftoken')) return
  const response = await fetch(`${API_BASE_URL}/auth/csrf/`, {
    credentials: 'include',
  })
  if (!response.ok) {
    throw new ApiError(response.status, await response.json().catch(() => ({})))
  }
}

type RequestOptions = Omit<RequestInit, 'body'> & {
  body?: unknown
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method?.toUpperCase() ?? 'GET'
  const headers = new Headers(options.headers)
  if (options.body !== undefined) headers.set('Content-Type', 'application/json')
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    await ensureCsrfToken()
    const csrfToken = getCookie('csrftoken')
    if (csrfToken) headers.set('X-CSRFToken', csrfToken)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: 'include',
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorShape
    throw new ApiError(response.status, body)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export type User = {
  id: number
  email: string
  first_name: string
  last_name: string
}

export type Organization = {
  id: number
  name: string
  slug: string
  my_role: string | null
}

export type League = { id: number; organization_id: number; name: string; slug: string; description: string }
export type Season = { id: number; league_id: number; name: string; start_date: string; end_date: string | null }
export type Team = { id: number; organization_id: number; name: string; slug: string }
export type Player = { id: number; organization_id: number; first_name: string; last_name: string; full_name: string }
export type SeasonTeam = { id: number; season_id: number; team_id: number; team_name: string }
export type RosterEntry = { id: number; season_team_id: number; player_id: number; player_name: string; shirt_number: number | null; position: string; is_captain: boolean }

export type Paginated<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type LoginInput = { email: string; password: string }
export type RegisterInput = LoginInput & {
  password_confirm: string
  first_name: string
  last_name: string
}

export const getCurrentUser = () => apiRequest<User>('/auth/me/')
export const login = (input: LoginInput) => apiRequest<User>('/auth/login/', { method: 'POST', body: input })
export const register = (input: RegisterInput) =>
  apiRequest<User>('/auth/register/', { method: 'POST', body: input })
export const logout = () => apiRequest<void>('/auth/logout/', { method: 'POST' })

async function list<T>(path: string): Promise<T[]> {
  const response = await apiRequest<T[] | Paginated<T>>(path)
  return Array.isArray(response) ? response : response.results
}

export const getOrganizations = () => list<Organization>('/organizations/')
export const createOrganization = (body: { name: string; slug: string }) =>
  apiRequest<Organization>('/organizations/', { method: 'POST', body })

export const getLeagues = (organizationId: number) => list<League>(`/organizations/${organizationId}/leagues/`)
export const createLeague = (organizationId: number, body: { name: string; slug: string; description: string }) =>
  apiRequest<League>(`/organizations/${organizationId}/leagues/`, { method: 'POST', body })

export const getSeasons = (organizationId: number, leagueId: number) =>
  list<Season>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/`)
export const createSeason = (organizationId: number, leagueId: number, body: { name: string; start_date: string; end_date?: string }) =>
  apiRequest<Season>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/`, { method: 'POST', body })

export const getTeams = (organizationId: number) => list<Team>(`/organizations/${organizationId}/teams/`)
export const createTeam = (organizationId: number, body: { name: string; slug: string }) =>
  apiRequest<Team>(`/organizations/${organizationId}/teams/`, { method: 'POST', body })

export const getPlayers = (organizationId: number) => list<Player>(`/organizations/${organizationId}/players/`)
export const createPlayer = (organizationId: number, body: { first_name: string; last_name: string; date_of_birth?: string }) =>
  apiRequest<Player>(`/organizations/${organizationId}/players/`, { method: 'POST', body })

export const getSeasonTeams = (organizationId: number, leagueId: number, seasonId: number) =>
  list<SeasonTeam>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/${seasonId}/teams/`)
export const addSeasonTeam = (organizationId: number, leagueId: number, seasonId: number, team_id: number) =>
  apiRequest<SeasonTeam>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/${seasonId}/teams/`, { method: 'POST', body: { team_id } })

export const getRoster = (organizationId: number, leagueId: number, seasonId: number, seasonTeamId: number) =>
  list<RosterEntry>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/${seasonId}/teams/${seasonTeamId}/roster/`)
export const addRosterEntry = (organizationId: number, leagueId: number, seasonId: number, seasonTeamId: number, body: { player_id: number; shirt_number?: number; position?: string; is_captain?: boolean }) =>
  apiRequest<RosterEntry>(`/organizations/${organizationId}/leagues/${leagueId}/seasons/${seasonId}/teams/${seasonTeamId}/roster/`, { method: 'POST', body })
