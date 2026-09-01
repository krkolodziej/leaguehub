import { ChevronRight } from 'lucide-react'
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
        /* Separate tiles rather than one ruled grid: with an odd number of
           organizations a ruled grid leaves an empty lit cell beside the last
           one, which reads as a missing card. */
        <ul className="grid gap-3 sm:grid-cols-2">
          {organizations.map((organization) => (
            <li key={organization.id} className="min-w-0">
              <Link
                className="group flex h-full items-center gap-3.5 rounded-[var(--radius-card)] border border-chalk bg-paper-raised px-4 py-4 shadow-panel transition-[border-color,box-shadow,transform] duration-150 hover:border-pitch/45 hover:shadow-lift focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pitch/40"
                to={`/organizations/${organization.id}`}
              >
                <TeamCrest name={organization.name} size="lg" />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="min-w-0 truncate font-condensed text-lg font-semibold text-ink">
                      {organization.name}
                    </span>
                    {organization.my_role && (
                      <span className="shrink-0 rounded-[var(--radius-control)] bg-pitch-wash px-1.5 py-0.5 font-condensed text-2xs font-bold uppercase tracking-[0.08em] text-pitch-dark">
                        {organization.my_role.toLowerCase()}
                      </span>
                    )}
                  </span>
                  <span className="mt-0.5 block truncate text-sm text-ink-muted">
                    /{organization.slug}
                  </span>
                </span>
                <ChevronRight
                  className="size-4 shrink-0 text-chalk transition-[color,transform] duration-150 group-hover:translate-x-0.5 group-hover:text-pitch"
                  aria-hidden="true"
                />
              </Link>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-6">
        <OrganizationForm />
      </div>
    </div>
  )
}
