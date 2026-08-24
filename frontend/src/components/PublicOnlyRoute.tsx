import { Navigate, Outlet } from 'react-router-dom'

import type { User } from '../lib/api'
import { LoadingState } from './LoadingState'

type PublicOnlyRouteProps = { user: User | undefined; isLoading: boolean }

export function PublicOnlyRoute({ user, isLoading }: PublicOnlyRouteProps) {
  if (isLoading) return <LoadingState label="Checking your session…" />
  if (user) return <Navigate to="/dashboard" replace />
  return <Outlet />
}
