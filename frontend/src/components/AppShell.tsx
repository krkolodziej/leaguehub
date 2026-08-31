import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useCurrentUser, useLogout } from '../lib/auth'
import { errorMessage } from '../lib/errors'
import { cn } from '../lib/utils'
import { Brand } from './Brand'
import { NotificationsMenu } from './NotificationsMenu'
import { Button } from './ui/button'

export function AppShell() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()
  const logoutMutation = useLogout()
  const displayName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.email

  const handleLogout = () => {
    logoutMutation.mutate(undefined, { onSuccess: () => navigate('/login', { replace: true }) })
  }

  return (
    <div className="min-h-screen bg-paper">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:bg-ink focus:px-3 focus:py-2 focus:text-sm focus:text-paper"
      >
        Skip to content
      </a>
      <header className="border-b-2 border-ink bg-paper-raised">
        <div className="mx-auto flex h-14 max-w-[1120px] items-center gap-4 px-4 sm:px-6">
          <Brand />
          <nav className="flex items-center" aria-label="Main">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                cn(
                  'border-b-2 px-1 pb-1 pt-1.5 font-condensed text-sm font-semibold',
                  isActive ? 'border-pitch text-ink' : 'border-transparent text-ink-muted hover:text-ink',
                )
              }
            >
              Dashboard
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <NotificationsMenu />
            <span className="hidden max-w-[16ch] truncate text-sm text-ink-muted md:inline">
              {displayName}
            </span>
            <Button variant="ghost" size="sm" onClick={handleLogout} disabled={logoutMutation.isPending}>
              {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
            </Button>
          </div>
        </div>
        {logoutMutation.isError && (
          <p
            className="border-t border-ink bg-paper px-4 py-2 text-sm font-medium text-ink sm:px-6"
            role="alert"
          >
            Could not sign out: {errorMessage(logoutMutation.error)}
          </p>
        )}
      </header>
      <main id="main" className="mx-auto max-w-[1120px] px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>
    </div>
  )
}
