import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useCurrentUser, useLogout } from '../lib/auth'
import { errorMessage } from '../lib/errors'
import { cn } from '../lib/utils'
import { Brand } from './Brand'
import { NotificationsMenu } from './NotificationsMenu'
import { TeamCrest } from './TeamCrest'
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
      {/* The masthead stays put: on a long fixture list the way back is always
          one click away. */}
      <header className="sticky top-0 z-40 border-b-2 border-ink bg-paper-raised/90 backdrop-blur supports-[backdrop-filter]:bg-paper-raised/75">
        <div className="mx-auto flex h-14 max-w-[1120px] items-center gap-3 px-4 sm:gap-5 sm:px-6">
          <Brand />
          <nav className="flex h-full items-center" aria-label="Main">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                cn(
                  'relative flex h-full items-center px-1 font-condensed text-sm font-semibold transition-colors',
                  'after:absolute after:inset-x-0 after:bottom-0 after:h-[3px] after:transition-colors',
                  isActive
                    ? 'text-ink after:bg-pitch'
                    : 'text-ink-muted after:bg-transparent hover:text-ink hover:after:bg-chalk',
                )
              }
            >
              Dashboard
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-1 sm:gap-2">
            <NotificationsMenu />
            {displayName && (
              <span className="hidden items-center gap-2 pl-1 pr-1 sm:flex sm:pr-2">
                <TeamCrest name={displayName} size="sm" />
                <span className="hidden max-w-[16ch] truncate text-sm text-ink-muted md:inline">
                  {displayName}
                </span>
              </span>
            )}
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
      <main id="main" className="mx-auto max-w-[1120px] px-4 py-7 sm:px-6 sm:py-9">
        <Outlet />
      </main>
    </div>
  )
}
