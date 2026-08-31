import { useMemo, useState, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'

import { BackLink } from '../components/BackLink'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { PageHeading } from '../components/PageHeading'
import { TeamCrest } from '../components/TeamCrest'
import { LeagueForm, PlayerForm, RosterForm, SeasonForm, SeasonTeamForm, TeamForm } from '../components/ManagementForms'
import { useOrganizations } from '../lib/organizations'
import { useLeagues, usePlayers, useRoster, useSeasonTeams, useSeasons, useTeams } from '../lib/management'

type Query = { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }

const SELECT_CLASS =
  'h-9 rounded-[2px] border border-chalk bg-paper-raised px-3 font-condensed text-sm font-semibold text-ink focus-visible:border-pitch'

export function OrganizationPage() {
  const { organizationId } = useParams()
  const id = Number(organizationId)
  const organizations = useOrganizations()
  const organization = organizations.data?.find((item) => item.id === id)
  const leagues = useLeagues(id)
  const teams = useTeams(id)
  const players = usePlayers(id)
  const [leagueId, setLeagueId] = useState<number>()
  const [seasonId, setSeasonId] = useState<number>()
  const [seasonTeamId, setSeasonTeamId] = useState<number>()
  const selectedLeagueId = leagueId ?? leagues.data?.[0]?.id
  const seasons = useSeasons(id, selectedLeagueId)
  const selectedSeasonId = seasonId ?? seasons.data?.[0]?.id
  const seasonTeams = useSeasonTeams(id, selectedLeagueId, selectedSeasonId)
  const selectedSeasonTeamId = seasonTeamId ?? seasonTeams.data?.[0]?.id
  const roster = useRoster(id, selectedLeagueId, selectedSeasonId, selectedSeasonTeamId)
  const assignedTeamIds = useMemo(() => new Set((seasonTeams.data ?? []).map((item) => item.team_id)), [seasonTeams.data])
  const availableTeams = (teams.data ?? []).filter((team) => !assignedTeamIds.has(team.id))
  const canManage = organization?.my_role === 'OWNER' || organization?.my_role === 'ADMIN'

  if (organizations.isPending) return <LoadingState label="Loading organization…" />
  if (organizations.isError) return <ErrorState error={organizations.error} retry={() => void organizations.refetch()} />
  if (!organization) return <ErrorState error={new Error('Organization not found, or you do not have access to it.')} />

  return (
    <div>
      <BackLink to="/dashboard">All organizations</BackLink>
      <PageHeading
        title={organization.name}
        subtitle={`/${organization.slug}`}
        meta={canManage ? 'Manager access' : `Your role: ${organization.my_role?.toLowerCase()}`}
      />

      <Section title="Leagues" description="Competitions run by this organization." count={leagues.data?.length}>
        <QueryArea query={leagues}>
          {leagues.data?.length === 0 ? (
            <EmptyState
              title="No leagues yet"
              action={canManage ? 'Add a league below, then give it a season and teams.' : 'An administrator needs to add a league before anything appears here.'}
            />
          ) : (
            <RuledList>
              {(leagues.data ?? []).map((league) => (
                <li key={league.id} className="flex items-center justify-between gap-4 px-4 py-3">
                  <span className="min-w-0">
                    <span className="block truncate font-condensed text-base font-semibold">{league.name}</span>
                    <span className="block truncate text-sm text-ink-muted">/{league.slug}</span>
                  </span>
                  <Link
                    className="shrink-0 text-sm font-semibold text-pitch underline-offset-4 hover:underline"
                    to={`/leagues/${league.id}?organization=${id}`}
                  >
                    Open dashboard
                  </Link>
                </li>
              ))}
            </RuledList>
          )}
        </QueryArea>
        {canManage && <LeagueForm organizationId={id} />}
      </Section>

      <Section title="Seasons" description="Pick a league, then manage the seasons inside it." count={seasons.data?.length}>
        {leagues.data && leagues.data.length > 0 && (
          <label className="mb-3 flex items-center gap-2 text-xs font-semibold tracking-wide text-ink-muted">
            League
            <select
              className={SELECT_CLASS}
              value={selectedLeagueId ?? ''}
              onChange={(event) => {
                setLeagueId(Number(event.target.value))
                setSeasonId(undefined)
                setSeasonTeamId(undefined)
              }}
            >
              <option value="">Choose league…</option>
              {leagues.data.map((league) => (
                <option key={league.id} value={league.id}>{league.name}</option>
              ))}
            </select>
          </label>
        )}
        <QueryArea query={seasons}>
          {(seasons.data ?? []).length === 0 ? (
            <EmptyState
              title="No seasons in this league"
              action={canManage ? 'Add a season below. Fixtures, tables and statistics all hang off a season.' : 'An administrator needs to add a season first.'}
            />
          ) : (
            <RuledList>
              {(seasons.data ?? []).map((season) => (
                <li key={season.id} className="flex items-center justify-between gap-4 px-4 py-3">
                  <span className="min-w-0">
                    <span className="block truncate font-condensed text-base font-semibold">{season.name}</span>
                    <span className="tabular block text-sm text-ink-muted">
                      {season.start_date}{season.end_date && ` – ${season.end_date}`}
                    </span>
                  </span>
                  <button
                    className={
                      selectedSeasonId === season.id
                        ? 'shrink-0 bg-ink px-2 py-1 font-condensed text-2xs font-semibold uppercase tracking-[0.08em] text-paper'
                        : 'shrink-0 border border-chalk px-2 py-1 font-condensed text-2xs font-semibold uppercase tracking-[0.08em] text-ink-muted hover:border-ink hover:text-ink'
                    }
                    onClick={() => {
                      setSeasonId(season.id)
                      setSeasonTeamId(undefined)
                    }}
                  >
                    {selectedSeasonId === season.id ? 'Selected' : 'Select'}
                  </button>
                </li>
              ))}
            </RuledList>
          )}
        </QueryArea>
        {canManage && selectedLeagueId && <SeasonForm organizationId={id} leagueId={selectedLeagueId} />}
      </Section>

      <div className="grid gap-8 lg:grid-cols-2">
        <Section title="Teams" description="Clubs registered to this organization." count={teams.data?.length}>
          <QueryArea query={teams}>
            {(teams.data ?? []).length === 0 ? (
              <EmptyState title="No teams yet" action={canManage ? 'Add clubs below, then attach them to a season.' : 'An administrator needs to add clubs first.'} />
            ) : (
              <RuledList>
                {(teams.data ?? []).map((team) => (
                  <li key={team.id} className="flex items-center gap-3 px-4 py-2.5">
                    <TeamCrest name={team.name} />
                    <span className="min-w-0 truncate font-condensed text-base font-semibold">{team.name}</span>
                  </li>
                ))}
              </RuledList>
            )}
          </QueryArea>
          {canManage && <TeamForm organizationId={id} />}
        </Section>

        <Section title="Players" description="Everyone available to a roster." count={players.data?.length}>
          <QueryArea query={players}>
            {(players.data ?? []).length === 0 ? (
              <EmptyState title="No players yet" action={canManage ? 'Add players below before building a season roster.' : 'An administrator needs to add players first.'} />
            ) : (
              <RuledList className="max-h-96 overflow-y-auto">
                {(players.data ?? []).map((player) => (
                  <li key={player.id} className="px-4 py-2.5 text-base">{player.full_name}</li>
                ))}
              </RuledList>
            )}
          </QueryArea>
          {canManage && <PlayerForm organizationId={id} />}
        </Section>
      </div>

      <Section title="Season rosters" description="Attach a club to the season, then name its squad." count={seasonTeams.data?.length}>
        {selectedLeagueId && selectedSeasonId && (
          <div className="mb-3 flex flex-wrap gap-3">
            <label className="flex items-center gap-2 text-xs font-semibold tracking-wide text-ink-muted">
              Season
              <select
                className={SELECT_CLASS}
                value={selectedSeasonId}
                onChange={(event) => {
                  setSeasonId(Number(event.target.value))
                  setSeasonTeamId(undefined)
                }}
              >
                {(seasons.data ?? []).map((season) => (
                  <option key={season.id} value={season.id}>{season.name}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 text-xs font-semibold tracking-wide text-ink-muted">
              Club
              <select
                className={SELECT_CLASS}
                value={selectedSeasonTeamId ?? ''}
                onChange={(event) => setSeasonTeamId(Number(event.target.value))}
              >
                <option value="">Choose club…</option>
                {(seasonTeams.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>{item.team_name}</option>
                ))}
              </select>
            </label>
          </div>
        )}
        {canManage && selectedLeagueId && selectedSeasonId && availableTeams.length > 0 && (
          <SeasonTeamForm organizationId={id} leagueId={selectedLeagueId} seasonId={selectedSeasonId} teams={availableTeams} />
        )}
        {selectedSeasonTeamId && (
          <div className="mt-4">
            <QueryArea query={roster}>
              {(roster.data ?? []).length === 0 ? (
                <EmptyState title="This squad is empty" action={canManage ? 'Add players to the squad below. Only rostered players can be credited with goals or cards.' : 'An administrator needs to name this squad.'} />
              ) : (
                <RuledList>
                  {(roster.data ?? []).map((entry) => (
                    <li key={entry.id} className="flex items-center gap-3 px-4 py-2.5">
                      <span className="tabular w-8 shrink-0 font-condensed text-sm font-semibold text-ink-muted">
                        {entry.shirt_number ?? '—'}
                      </span>
                      <span className="min-w-0 flex-1 truncate text-base">{entry.player_name}</span>
                      {entry.is_captain && (
                        <span className="shrink-0 border border-ink px-1 font-condensed text-2xs font-bold" title="Captain">C</span>
                      )}
                      {entry.position && (
                        <span className="shrink-0 text-sm text-ink-muted">{entry.position}</span>
                      )}
                    </li>
                  ))}
                </RuledList>
              )}
            </QueryArea>
            {canManage && selectedLeagueId && selectedSeasonId && (
              <RosterForm
                organizationId={id}
                leagueId={selectedLeagueId}
                seasonId={selectedSeasonId}
                seasonTeamId={selectedSeasonTeamId}
                players={(players.data ?? []).map((player) => ({ id: player.id, full_name: player.full_name }))}
              />
            )}
          </div>
        )}
      </Section>
    </div>
  )
}

function Section({ title, description, count, children }: { title: string; description: string; count?: number; children: ReactNode }) {
  return (
    <section className="mt-8 first:mt-0 min-w-0">
      <div className="mb-3 flex items-baseline justify-between gap-4 border-b border-chalk pb-1.5">
        <div>
          <h2 className="text-lg leading-tight">{title}</h2>
          <p className="text-sm text-ink-muted">{description}</p>
        </div>
        {count !== undefined && (
          <span className="tabular font-condensed text-sm font-semibold text-ink-muted">{count}</span>
        )}
      </div>
      {children}
    </section>
  )
}

function QueryArea({ query, children }: { query: Query; children: ReactNode }) {
  if (query.isPending) return <LoadingState rows={3} />
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />
  return <>{children}</>
}

function RuledList({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <ul className={`divide-y divide-chalk border border-chalk bg-paper-raised ${className ?? ''}`}>
      {children}
    </ul>
  )
}
