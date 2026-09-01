import { Outlet } from 'react-router-dom'

import { Brand } from '../components/Brand'

export function AuthLayout() {
  return (
    <div className="grid min-h-screen grid-rows-[1fr_auto] bg-paper px-4 py-8">
      <main className="grid place-items-center">
        <div className="w-full max-w-[26rem] rounded-[var(--radius-card)] border border-chalk bg-paper-raised p-6 shadow-panel sm:p-8">
          <Brand to="/" />
          <Outlet />
        </div>
      </main>
      <p className="pt-8 text-center text-xs text-ink-muted">
        LeagueHub — amateur league administration.
      </p>
    </div>
  )
}
