import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useCurrentUser, useLogout } from '../lib/auth'
import { NotificationsMenu } from './NotificationsMenu'

export function AppShell() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()
  const logoutMutation = useLogout()
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email

  const handleLogout = () => {
    logoutMutation.mutate(undefined, { onSuccess: () => navigate('/login', { replace: true }) })
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/dashboard"><span className="brand-mark">L</span>LeagueHub</Link>
        <nav className="topnav" aria-label="Main navigation">
          <NavLink className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'} to="/dashboard">Dashboard</NavLink>
        </nav>
        <div className="user-menu">
          <NotificationsMenu />
          <span className="user-name">{displayName}</span>
          <button className="button button-ghost" onClick={handleLogout} disabled={logoutMutation.isPending}>
            {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </header>
      <main className="page-content"><Outlet /></main>
    </div>
  )
}
