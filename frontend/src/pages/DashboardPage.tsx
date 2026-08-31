import { Link } from 'react-router-dom'

import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { OrganizationForm } from '../components/ManagementForms'
import { PageHeading } from '../components/PageHeading'
import { TeamCrest } from '../components/TeamCrest'
import { useOrganizations } from '../lib/organizations'

export function DashboardPage() {
  const organizationsQuery = useOrganizations()
  if (organizationsQuery.isPending) return <LoadingState label="Loading your organizations…" />
  if (organizationsQuery.isError)
    return <ErrorState error={organizationsQuery.error} retry={() => void organizationsQuery.refetch()} />
  const organizations = organizationsQuery.data

  return (
    <div>
      <PageHeading
        title="Your organizations"
        subtitle="Every association and club office you belong to."
        meta={`${organizations.length} ${organizations.length === 1 ? 'organization' : 'organizations'}`}
      />
      {organizations.length === 0 ? (
        <EmptyState
          title="No organizations yet"
          action="Create one below to start a league. You will be its owner, and can invite administrators afterwards."
        />
      ) : (
        <ul className="grid gap-px border border-chalk bg-chalk sm:grid-cols-2">
          {organizations.map((organization) => (
            <li key={organization.id} className="min-w-0 bg-paper-raised">
              <Link
                className="flex items-center gap-3 px-4 py-4 hover:bg-pitch-wash"
                to={`/organizations/${organization.id}`}
              >
                <TeamCrest name={organization.name} size="lg" />
                <span className="min-w-0">
                  <span className="flex items-baseline gap-2">
                    <span className="min-w-0 truncate font-condensed text-lg font-semibold text-ink">
                      {organization.name}
                    </span>
                    {organization.my_role && (
                      <span className="shrink-0 border border-chalk px-1.5 font-condensed text-2xs font-semibold uppercase tracking-[0.08em] text-ink-muted">
                        {organization.my_role.toLowerCase()}
                      </span>
                    )}
                  </span>
                  <span className="mt-0.5 block truncate text-sm text-ink-muted">
                    /{organization.slug}
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <OrganizationForm />
    </div>
  )
}
