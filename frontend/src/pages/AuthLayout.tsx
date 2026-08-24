import { Link, Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <main className="auth-page">
      <section className="auth-aside">
        <Link className="brand brand-light" to="/"><span className="brand-mark">L</span>LeagueHub</Link>
        <div>
          <p className="eyebrow">Your league, organized</p>
          <h1>Make every match count.</h1>
          <p className="aside-copy">A calm home for your organizations, teams, fixtures and results.</p>
        </div>
      </section>
      <section className="auth-panel"><Outlet /></section>
    </main>
  )
}
