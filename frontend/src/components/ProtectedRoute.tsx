import { Navigate, Outlet, useLocation } from 'react-router-dom'

import type { User } from '../lib/api'
import { LoadingState } from './LoadingState'

type ProtectedRouteProps = { user: User | undefined; isLoading: boolean }

export function ProtectedRoute({ user, isLoading }: ProtectedRouteProps) {
  const location = useLocation()
  if (isLoading) return <LoadingState label="Checking your session…" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
