import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom'
import type { ReactNode } from 'react'

import { BackLink } from '../components/BackLink'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { FixtureRow } from '../components/FixtureRow'
import { LoadingState } from '../components/LoadingState'
import { MatchStatus } from '../components/MatchStatus'
import { MatchTimeline } from '../components/MatchTimeline'
import { PageHeading } from '../components/PageHeading'
import { ScoreLine } from '../components/ScoreLine'
import { StandingsTable } from '../components/StandingsTable'
import { TeamCrest } from '../components/TeamCrest'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { useOrganizations } from '../lib/organizations'
import { useFixtures, useLeagues, useMatches, useMatch, useMatchEvents, usePlayerStatistics, useRoster, useSeasonTeams, useSeasons, useStandings, useTopScorers } from '../lib/management'
import type { Fixture, Match, PlayerStatistic, SeasonTeam, Standing } from '../lib/api'
import { cn } from '../lib/utils'
import { useLiveMatch } from '../lib/realtime'

type DashboardView = 'overview' | 'fixtures' | 'table' | 'teams' | 'statistics'
type Query = { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }

const VIEWS: DashboardView[] = ['overview', 'fixtures', 'table', 'teams', 'statistics']
const VIEW_LABELS: Record<DashboardView, string> = {
  overview: 'Overview',
  fixtures: 'Fixtures',
  table: 'Table',
  teams: 'Teams',
  statistics: 'Statistics',
}

export function LeagueDashboardPage() {
  const location = useLocation()
  const { leagueId: leagueParam } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const organizationId = Number(searchParams.get('organization')) || undefined
  const leagueId = Number(leagueParam) || undefined
  const seasonParam = Number(searchParams.get('season')) || undefined
  const view = getDashboardView(location.pathname)
  const organizations = useOrganizations(Boolean(organizationId))
  const leagues = useLeagues(organizationId)
  const league = leagues.data?.find((item) => item.id === leagueId)
  const seasons = useSeasons(organizationId, leagueId)
  const seasonId = seasonParam ?? seasons.data?.[0]?.id
  const fixtures = useFixtures(organizationId, leagueId, seasonId)
  const matches = useMatches(organizationId, leagueId, seasonId)
  const standings = useStandings(organizationId, leagueId, seasonId)
  const topScorers = useTopScorers(organizationId, leagueId, seasonId)
  const statistics = usePlayerStatistics(organizationId, leagueId, seasonId)
  const seasonTeams = useSeasonTeams(organizationId, leagueId, seasonId)

  if (!organizationId || !leagueId) return <ErrorState error={new Error('This league link is missing its organization context.')} />
  if (organizations.isPending || leagues.isPending) return <LoadingState label="Loading league…" />
  if (organizations.isError) return <ErrorState error={organizations.error} retry={() => void organizations.refetch()} />
  if (leagues.isError) return <ErrorState error={leagues.error} retry={() => void leagues.refetch()} />
  if (!league) return <ErrorState error={new Error('League not found, or you do not have access to it.')} />

  const organization = organizations.data?.find((item) => item.id === organizationId)
  const season = seasons.data?.find((item) => item.id === seasonId)
  const setSeason = (value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set('season', value)
    else next.delete('season')
    setSearchParams(next)
  }

  return (
    <div>
      <BackLink to={organization ? `/organizations/${organization.id}` : '/dashboard'}>
        {organization ? organization.name : 'Dashboard'}
      </BackLink>
      <PageHeading title={league.name} subtitle={league.description || `/${league.slug}`}>
        {seasons.data && seasons.data.length > 0 && (
          <label className="flex items-center gap-2 text-xs font-semibold tracking-wide text-ink-muted">
            Season
            <Select value={seasonId ? String(seasonId) : undefined} onValueChange={setSeason}>
              <SelectTrigger className="min-w-32" aria-label="Season">
                <SelectValue placeholder="Choose season" />
              </SelectTrigger>
              <SelectContent>
                {seasons.data.map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>{item.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>
        )}
      </PageHeading>

      <nav className="-mt-2 mb-6 flex gap-5 overflow-x-auto border-b border-chalk" aria-label="League sections">
        {VIEWS.map((tab) => (
          <Link
            key={tab}
            className={cn(
              'shrink-0 border-b-2 pb-2 font-condensed text-base font-semibold transition-colors',
              view === tab ? 'border-pitch text-ink' : 'border-transparent text-ink-muted hover:text-ink',
            )}
            aria-current={view === tab ? 'page' : undefined}
            to={dashboardPath(leagueId, tab, organizationId, seasonId)}
          >
            {VIEW_LABELS[tab]}
          </Link>
        ))}
      </nav>

      {!seasonId || seasons.data?.length === 0 ? (
        <EmptyState
          title="This league has no season yet"
          action="Add a season from the organization page. Fixtures, the table and statistics all belong to a season."
        />
      ) : view === 'fixtures' ? (
        <FixturesView fixtures={fixtures.data ?? []} matches={matches.data ?? []} query={fixtures} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} />
      ) : view === 'table' ? (
        <StandingsView standings={standings.data ?? []} matches={matches.data ?? []} query={standings} />
      ) : view === 'teams' ? (
        <TeamsView teams={seasonTeams.data ?? []} query={seasonTeams} />
      ) : view === 'statistics' ? (
        <StatisticsView statistics={statistics.data ?? []} topScorers={topScorers.data ?? []} statisticsQuery={statistics} scorersQuery={topScorers} />
      ) : (
        <OverviewView
          fixtures={fixtures.data ?? []}
          matches={matches.data ?? []}
          standings={standings.data ?? []}
          scorers={topScorers.data ?? []}
          queries={{ fixtures, matches, standings, topScorers }}
          organizationId={organizationId}
          leagueId={leagueId}
          seasonId={seasonId}
          seasonName={season?.name}
        />
      )}
    </div>
  )
}

export function MatchPage() {
  const { matchId: matchParam, leagueId: leagueParam } = useParams()
  const [searchParams] = useSearchParams()
  const organizationId = Number(searchParams.get('organization')) || undefined
  const leagueId = Number(leagueParam) || Number(searchParams.get('league')) || undefined
  const seasonId = Number(searchParams.get('season')) || undefined
  const matchId = Number(matchParam) || undefined
  const match = useMatch(organizationId, leagueId, seasonId, matchId)
  const events = useMatchEvents(organizationId, leagueId, seasonId, matchId)
  const liveStatus = useLiveMatch(organizationId, leagueId, seasonId, matchId)
  const seasonTeams = useSeasonTeams(organizationId, leagueId, seasonId)

  // Events carry player IDs only, so the two squads supply the names.
  const homeSeasonTeam = seasonTeams.data?.find((item) => item.team_id === match.data?.home_team_id)
  const awaySeasonTeam = seasonTeams.data?.find((item) => item.team_id === match.data?.away_team_id)
  const homeRoster = useRoster(organizationId, leagueId, seasonId, homeSeasonTeam?.id)
  const awayRoster = useRoster(organizationId, leagueId, seasonId, awaySeasonTeam?.id)
  const playerNames = new Map(
    [...(homeRoster.data ?? []), ...(awayRoster.data ?? [])].map((entry) => [entry.player_id, entry.player_name]),
  )

  if (!organizationId || !leagueId || !seasonId) return <ErrorState error={new Error('This match link is missing its organization and season context.')} />
  if (match.isPending) return <LoadingState label="Loading match…" />
  if (match.isError) return <ErrorState error={match.error} retry={() => void match.refetch()} />
  if (!match.data) return <ErrorState error={new Error('Match not found.')} />

  const item = match.data
  const played = item.status === 'FINISHED' || item.status === 'LIVE'

  return (
    <div>
      <BackLink to={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)}>Fixtures</BackLink>
      <section className="border border-chalk bg-paper-raised">
        <div className="flex items-center justify-between gap-3 border-b border-chalk px-4 py-2">
          <MatchStatus status={item.status} />
          {item.status === 'LIVE' && (
            <span className="text-2xs text-ink-muted">
              {liveStatus === 'connected' ? 'Updating automatically' : liveStatus === 'reconnecting' ? 'Reconnecting…' : 'Connecting…'}
            </span>
          )}
        </div>
        <div className="px-4 py-7 sm:px-8 sm:py-10">
          <ScoreLine
            homeTeam={item.home_team_name}
            awayTeam={item.away_team_name}
            homeScore={item.home_score}
            awayScore={item.away_score}
            played={played}
            kickoff={item.started_at}
          />
        </div>
      </section>

      <Panel title="Match events" description="Goals and cards, arriving without a refresh while a match is live.">
        <QueryArea query={events}>
          {(events.data ?? []).length === 0 ? (
            <EmptyState
              title="Nothing has happened yet"
              action={played ? 'Goals and cards will appear here as officials record them.' : 'Events appear once this match kicks off.'}
            />
          ) : (
            <MatchTimeline
              events={events.data ?? []}
              homeTeamId={item.home_team_id}
              homeTeamName={item.home_team_name}
              awayTeamName={item.away_team_name}
              playerNames={playerNames}
            />
          )}
        </QueryArea>
      </Panel>
    </div>
  )
}

function OverviewView({ fixtures, matches, standings, scorers, queries, organizationId, leagueId, seasonId, seasonName }: {
  fixtures: Fixture[]
  matches: Match[]
  standings: Standing[]
  scorers: PlayerStatistic[]
  queries: Record<string, Query>
  organizationId: number
  leagueId: number
  seasonId: number
  seasonName?: string
}) {
  const matchByFixture = new Map(matches.map((match) => [match.fixture_id, match]))
  const upcoming = fixtures
    .filter((fixture) => {
      // Postponed games have lost their date, so they belong in the full
      // fixture list rather than in a panel promising what is next.
      const status = matchByFixture.get(fixture.id)?.status ?? 'SCHEDULED'
      return status === 'LIVE' || status === 'SCHEDULED'
    })
    .sort((a, b) => {
      const live = Number(matchByFixture.get(b.id)?.status === 'LIVE') - Number(matchByFixture.get(a.id)?.status === 'LIVE')
      return live || (a.scheduled_at ?? '').localeCompare(b.scheduled_at ?? '')
    })
    .slice(0, 4)
  const recent = matches
    .filter((match) => match.status === 'FINISHED')
    .sort((a, b) => (b.finished_at ?? '').localeCompare(a.finished_at ?? ''))
    .slice(0, 4)

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <Panel title="Next matches" description={seasonName ? `Season ${seasonName}` : undefined} link={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)}>
        <QueryArea query={queries.fixtures}>
          {upcoming.length === 0 ? (
            <EmptyState title="Nothing left to play" action="Every fixture in this season has a result. Open the table to see how it finished." />
          ) : (
            <RuledList>
              {upcoming.map((fixture) => (
                <li key={fixture.id}>
                  <FixtureRow
                    round={fixture.round_number}
                    homeTeam={fixture.home_team_name}
                    awayTeam={fixture.away_team_name}
                    kickoff={fixture.scheduled_at}
                    match={matchByFixture.get(fixture.id)}
                    href={matchHref(matchByFixture.get(fixture.id), organizationId, leagueId, seasonId)}
                  />
                </li>
              ))}
            </RuledList>
          )}
        </QueryArea>
      </Panel>

      <Panel title="Table" link={dashboardPath(leagueId, 'table', organizationId, seasonId)}>
        <QueryArea query={queries.standings}>
          {standings.length === 0 ? (
            <EmptyState title="The table is empty" action="It fills in as soon as the first match is marked finished." />
          ) : (
            <MiniTable rows={standings} />
          )}
        </QueryArea>
      </Panel>

      <Panel title="Recent results" link={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)}>
        <QueryArea query={queries.matches}>
          {recent.length === 0 ? (
            <EmptyState title="No results yet" action="Finished matches show up here with their scores." />
          ) : (
            <RuledList>
              {recent.map((match) => (
                <li key={match.id}>
                  <FixtureRow
                    round={0}
                    homeTeam={match.home_team_name}
                    awayTeam={match.away_team_name}
                    kickoff={match.finished_at}
                    match={match}
                    href={matchHref(match, organizationId, leagueId, seasonId)}
                  />
                </li>
              ))}
            </RuledList>
          )}
        </QueryArea>
      </Panel>

      <Panel title="Top scorers" link={dashboardPath(leagueId, 'statistics', organizationId, seasonId)}>
        <QueryArea query={queries.topScorers}>
          {scorers.length === 0 ? (
            <EmptyState title="No goals recorded" action="Scorers appear once goals are logged against a finished match." />
          ) : (
            <ScorerList players={scorers.slice(0, 6)} />
          )}
        </QueryArea>
      </Panel>
    </div>
  )
}

function FixturesView({ fixtures, matches, query, organizationId, leagueId, seasonId }: {
  fixtures: Fixture[]
  matches: Match[]
  query: Query
  organizationId: number
  leagueId: number
  seasonId: number
}) {
  const matchByFixture = new Map(matches.map((match) => [match.fixture_id, match]))
  const rounds = fixtures.reduce<Map<number, Fixture[]>>((accumulator, fixture) => {
    const bucket = accumulator.get(fixture.round_number) ?? []
    bucket.push(fixture)
    accumulator.set(fixture.round_number, bucket)
    return accumulator
  }, new Map())

  return (
    <Panel title="Fixtures" description="The full season schedule, round by round.">
      <QueryArea query={query}>
        {fixtures.length === 0 ? (
          <EmptyState title="No fixtures yet" action="Generate the schedule for this season from the organization page." />
        ) : (
          <div className="space-y-6">
            {[...rounds.entries()].map(([round, roundFixtures]) => (
              <section key={round}>
                <h3 className="mb-1.5 font-condensed text-sm font-semibold text-ink-muted">Round {round}</h3>
                <RuledList>
                  {roundFixtures.map((fixture) => (
                    <li key={fixture.id}>
                      <FixtureRow
                        round={fixture.round_number}
                        homeTeam={fixture.home_team_name}
                        awayTeam={fixture.away_team_name}
                        kickoff={fixture.scheduled_at}
                        match={matchByFixture.get(fixture.id)}
                        href={matchHref(matchByFixture.get(fixture.id), organizationId, leagueId, seasonId)}
                      />
                    </li>
                  ))}
                </RuledList>
              </section>
            ))}
          </div>
        )}
      </QueryArea>
    </Panel>
  )
}

function StandingsView({ standings, matches, query }: { standings: Standing[]; matches: Match[]; query: Query }) {
  return (
    <Panel title="Table" description="Finished matches only, ordered by points, then goal difference.">
      <QueryArea query={query}>
        {standings.length === 0 ? (
          <EmptyState title="The table is empty" action="It fills in as soon as the first match is marked finished." />
        ) : (
          <StandingsTable standings={standings} matches={matches} />
        )}
      </QueryArea>
    </Panel>
  )
}

function TeamsView({ teams, query }: { teams: SeasonTeam[]; query: Query }) {
  return (
    <Panel title="Clubs" description="Everyone registered for this season.">
      <QueryArea query={query}>
        {teams.length === 0 ? (
          <EmptyState title="No clubs registered" action="Attach clubs to this season from the organization page, then generate fixtures." />
        ) : (
          <ul className="grid gap-px border border-chalk bg-chalk sm:grid-cols-2 lg:grid-cols-3">
            {teams.map((team) => (
              <li key={team.id} className="flex items-center gap-3 bg-paper-raised px-4 py-3">
                <TeamCrest name={team.team_name} size="lg" />
                <span className="truncate font-condensed text-base font-semibold text-ink">{team.team_name}</span>
              </li>
            ))}
          </ul>
        )}
      </QueryArea>
    </Panel>
  )
}

function StatisticsView({ statistics, topScorers, statisticsQuery, scorersQuery }: {
  statistics: PlayerStatistic[]
  topScorers: PlayerStatistic[]
  statisticsQuery: Query
  scorersQuery: Query
}) {
  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <Panel title="Top scorers" description="Goals in finished matches.">
        <QueryArea query={scorersQuery}>
          {topScorers.length === 0 ? (
            <EmptyState title="No goals recorded" action="Scorers appear once goals are logged against a finished match." />
          ) : (
            <ScorerList players={topScorers} />
          )}
        </QueryArea>
      </Panel>

      <Panel title="Discipline and appearances" description="Every player with recorded activity this season.">
        <QueryArea query={statisticsQuery}>
          {statistics.length === 0 ? (
            <EmptyState title="No statistics yet" action="These fill in from match events as results are recorded." />
          ) : (
            <div className="overflow-x-auto border border-chalk bg-paper-raised">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b-2 border-ink">
                    <th scope="col" className="px-3 py-1.5 text-left font-condensed text-2xs font-semibold uppercase tracking-[0.06em] text-ink-muted">Player</th>
                    <th scope="col" className="px-2 py-1.5 text-right font-condensed text-2xs font-semibold uppercase tracking-[0.06em] text-ink-muted">Goals</th>
                    <th scope="col" className="px-2 py-1.5 text-right font-condensed text-2xs font-semibold uppercase tracking-[0.06em] text-ink-muted">
                      <span className="sr-only">Yellow cards</span>
                      <span className="inline-block h-3.5 w-2.5 rounded-[1px] bg-booking align-middle" aria-hidden="true" />
                    </th>
                    <th scope="col" className="px-3 py-1.5 text-right font-condensed text-2xs font-semibold uppercase tracking-[0.06em] text-ink-muted">
                      <span className="sr-only">Red cards</span>
                      <span className="inline-block h-3.5 w-2.5 rounded-[1px] bg-sending-off align-middle" aria-hidden="true" />
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {statistics.map((player) => (
                    <tr key={player.id} className="border-b border-chalk last:border-b-0">
                      <th scope="row" className="px-3 py-2 text-left font-normal">{player.full_name}</th>
                      <td className="px-2 py-2 text-right font-condensed font-bold tabular-nums">{player.goals}</td>
                      <td className="px-2 py-2 text-right tabular-nums text-ink-muted">{player.yellow_cards}</td>
                      <td className="px-3 py-2 text-right tabular-nums text-ink-muted">{player.red_cards}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </QueryArea>
      </Panel>
    </div>
  )
}

function ScorerList({ players }: { players: PlayerStatistic[] }) {
  return (
    <RuledList>
      {players.map((player, index) => (
        <li key={player.id} className="flex items-center gap-3 px-3 py-2.5">
          <span className="tabular w-5 shrink-0 text-right font-condensed text-sm font-semibold text-ink-muted">
            {index + 1}
          </span>
          <span className="min-w-0 flex-1 truncate text-base">{player.full_name}</span>
          <span className="tabular shrink-0 font-condensed text-lg font-bold text-ink">{player.goals}</span>
        </li>
      ))}
    </RuledList>
  )
}

function MiniTable({ rows }: { rows: Standing[] }) {
  // Head and tail of the division: who is going up, and who is in trouble.
  const head = rows.slice(0, 5)
  const tail = rows.length > 7 ? rows.slice(-2) : []
  const render = (row: Standing, position: number) => (
    <li key={row.team_id} className="flex items-center gap-3 px-3 py-2">
      <span className="tabular w-5 shrink-0 text-right font-condensed text-sm font-semibold text-ink-muted">{position}</span>
      <TeamCrest name={row.team_name} size="sm" />
      <span className="min-w-0 flex-1 truncate font-condensed text-base font-semibold">{row.team_name}</span>
      <span className="tabular shrink-0 text-sm text-ink-muted">{row.mp}</span>
      <span className="tabular w-7 shrink-0 text-right font-condensed text-base font-bold">{row.pts}</span>
    </li>
  )
  return (
    <RuledList>
      {head.map((row, index) => render(row, index + 1))}
      {tail.length > 0 && (
        <li className="px-3 py-1 text-center text-2xs text-ink-muted" aria-hidden="true">⋯</li>
      )}
      {tail.map((row, index) => render(row, rows.length - tail.length + index + 1))}
    </RuledList>
  )
}

function Panel({ title, description, link, children }: { title: string; description?: string; link?: string; children: ReactNode }) {
  return (
    <section>
      <div className="mb-3 flex items-baseline justify-between gap-4 border-b border-chalk pb-1.5">
        <div className="min-w-0">
          <h2 className="text-lg leading-tight">{title}</h2>
          {description && <p className="text-sm text-ink-muted">{description}</p>}
        </div>
        {link && (
          <Link className="shrink-0 text-sm font-semibold text-pitch underline-offset-4 hover:underline" to={link}>
            View all
          </Link>
        )}
      </div>
      {children}
    </section>
  )
}

function QueryArea({ query, children }: { query: Query; children: ReactNode }) {
  if (query.isPending) return <LoadingState rows={4} />
  if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />
  return <>{children}</>
}

function RuledList({ children }: { children: ReactNode }) {
  return <ul className="divide-y divide-chalk border border-chalk bg-paper-raised">{children}</ul>
}

function matchHref(match: Match | undefined, organizationId: number, leagueId: number, seasonId: number) {
  return match ? `/matches/${match.id}?organization=${organizationId}&league=${leagueId}&season=${seasonId}` : undefined
}

function getDashboardView(pathname: string): DashboardView {
  const segment = pathname.split('/').filter(Boolean).pop()
  return segment === 'fixtures' || segment === 'table' || segment === 'teams' || segment === 'statistics' ? segment : 'overview'
}

function dashboardPath(leagueId: number, view: DashboardView, organizationId: number, seasonId?: number) {
  const suffix = view === 'overview' ? '' : `/${view}`
  const season = seasonId ? `&season=${seasonId}` : ''
  return `/leagues/${leagueId}${suffix}?organization=${organizationId}${season}`
}
