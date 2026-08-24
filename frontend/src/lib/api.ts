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

export async function getOrganizations(): Promise<Organization[]> {
  const response = await apiRequest<Organization[] | Paginated<Organization>>('/organizations/')
  return Array.isArray(response) ? response : response.results
}
