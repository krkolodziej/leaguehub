import { Link } from 'react-router-dom'

import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { OrganizationForm } from '../components/ManagementForms'
import { useOrganizations } from '../lib/organizations'

export function DashboardPage() {
  const organizationsQuery = useOrganizations()
  if (organizationsQuery.isPending) return <LoadingState label="Loading your organizations…" />
  if (organizationsQuery.isError) return <ErrorState error={organizationsQuery.error} retry={() => void organizationsQuery.refetch()} />
  const organizations = organizationsQuery.data

  return (
    <div className="dashboard-page">
      <div className="page-heading"><div><p className="eyebrow">Workspace</p><h1>Your organizations</h1><p className="muted">Everything you belong to, in one place.</p></div><span className="count-pill">{organizations.length} {organizations.length === 1 ? 'organization' : 'organizations'}</span></div>
      <OrganizationForm />
      {organizations.length === 0 ? (
        <section className="empty-card"><div className="empty-icon">+</div><h2>No organizations yet</h2><p className="muted">Your organizations will appear here when you join or create one.</p></section>
      ) : (
        <div className="organization-grid">{organizations.map((organization) => <article className="organization-card" key={organization.id}><div className="org-avatar">{organization.name.slice(0, 1).toUpperCase()}</div><div className="org-content"><div className="org-title-row"><h2>{organization.name}</h2>{organization.my_role && <span className="role-badge">{organization.my_role.toLowerCase()}</span>}</div><p className="muted">/{organization.slug}</p><Link className="text-link" to={`/organizations/${organization.id}`}>Open organization <span aria-hidden="true">→</span></Link></div></article>)}</div>
      )}
    </div>
  )
}
