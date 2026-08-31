import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { PublicOnlyRoute } from './components/PublicOnlyRoute'
import { useCurrentUser } from './lib/auth'
import { AuthLayout } from './pages/AuthLayout'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { OrganizationPage } from './pages/OrganizationPage'
import { LeagueDashboardPage, MatchPage } from './pages/LeagueDashboardPage'
import { RegisterPage } from './pages/RegisterPage'

function App() {
  const auth = useCurrentUser()

  return (
    <Routes>
      <Route element={<PublicOnlyRoute user={auth.data} isLoading={auth.isPending} />}>
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
      </Route>
      <Route element={<ProtectedRoute user={auth.data} isLoading={auth.isPending} />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/organizations/:organizationId" element={<OrganizationPage />} />
          <Route path="/leagues/:leagueId" element={<LeagueDashboardPage />} />
          <Route path="/leagues/:leagueId/:view" element={<LeagueDashboardPage />} />
          <Route path="/matches/:matchId" element={<MatchPage />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
