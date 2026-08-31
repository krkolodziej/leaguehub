import { Link, Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <main className="auth-page">
      <div className="auth-card">
        <Link className="brand" to="/"><span className="brand-mark">L</span>LeagueHub</Link>
        <Outlet />
      </div>
    </main>
  )
}
