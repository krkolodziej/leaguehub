import { Link, useLocation, useParams, useSearchParams } from 'react-router-dom'
import type { ReactNode } from 'react'

import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { useOrganizations } from '../lib/organizations'
import { useFixtures, useLeagues, useMatches, useMatch, useMatchEvents, usePlayerStatistics, useSeasonTeams, useSeasons, useStandings, useTopScorers } from '../lib/management'
import type { Fixture, Match, MatchEvent, PlayerStatistic, Standing } from '../lib/api'
import { useLiveMatch } from '../lib/realtime'

type DashboardView = 'overview' | 'fixtures' | 'table' | 'teams' | 'statistics'

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
  if (!league) return <ErrorState error={new Error('League not found or you do not have access.')} />

  const organization = organizations.data?.find((item) => item.id === organizationId)
  const setSeason = (value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set('season', value)
    else next.delete('season')
    setSearchParams(next)
  }

  return (
    <div className="league-page">
      <Link className="back-link" to={organization ? `/organizations/${organization.id}` : '/dashboard'}>← Back to organization</Link>
      <header className="league-hero">
        <div><p className="eyebrow">League dashboard</p><h1>{league.name}</h1><p className="muted">/{league.slug}{league.description && ` · ${league.description}`}</p></div>
        {seasons.data && seasons.data.length > 0 && <label className="season-picker">Season<select className="select-control" value={seasonId ?? ''} onChange={(event) => setSeason(event.target.value)}>{seasons.data.map((season) => <option key={season.id} value={season.id}>{season.name}</option>)}</select></label>}
      </header>
      <nav className="dashboard-tabs" aria-label="League sections">{(['overview', 'fixtures', 'table', 'teams', 'statistics'] as DashboardView[]).map((tab) => <Link key={tab} className={view === tab ? 'dashboard-tab active' : 'dashboard-tab'} to={dashboardPath(leagueId, tab, organizationId, seasonId)}>{tab === 'table' ? 'Table' : tab[0].toUpperCase() + tab.slice(1)}</Link>)}</nav>
      {!seasonId || seasons.data?.length === 0 ? <EmptyCard title="No season yet" text="Create a season in the organization management view before opening the league dashboard." /> : view === 'fixtures' ? <FixturesView fixtures={fixtures.data ?? []} matches={matches.data ?? []} query={fixtures} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} /> : view === 'table' ? <StandingsView standings={standings.data ?? []} query={standings} /> : view === 'teams' ? <TeamsView teams={seasonTeams.data ?? []} query={seasonTeams} /> : view === 'statistics' ? <StatisticsView statistics={statistics.data ?? []} topScorers={topScorers.data ?? []} statisticsQuery={statistics} scorersQuery={topScorers} /> : <OverviewView fixtures={fixtures.data ?? []} matches={matches.data ?? []} standings={standings.data ?? []} scorers={topScorers.data ?? []} queries={{ fixtures, matches, standings, topScorers }} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} />}
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
  if (!organizationId || !leagueId || !seasonId) return <ErrorState error={new Error('This match link is missing organization and season context.')} />
  if (match.isPending) return <LoadingState label="Loading match…" />
  if (match.isError) return <ErrorState error={match.error} retry={() => void match.refetch()} />
  if (!match.data) return <ErrorState error={new Error('Match not found.')} />
  const item = match.data
  return <div className="league-page"><Link className="back-link" to={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)}>← Back to fixtures</Link><section className="match-card match-detail"><div className="match-heading"><p className="eyebrow">Match #{item.id} · {item.status.toLowerCase()}</p><span className={`live-status ${liveStatus}`}>{liveStatus === 'connected' ? 'Live updates connected' : liveStatus === 'reconnecting' ? 'Reconnecting…' : 'Connecting…'}</span></div><div className="scoreline"><div><strong>{item.home_team_name}</strong><span>{item.home_score}</span></div><div className="score-divider">:</div><div><strong>{item.away_team_name}</strong><span>{item.away_score}</span></div></div><p className="muted">Fixture #{item.fixture_id}</p></section><EventTimeline events={events.data ?? []} query={events} /></div>
}

function OverviewView({ fixtures, matches, standings, scorers, queries, organizationId, leagueId, seasonId }: { fixtures: Fixture[]; matches: Match[]; standings: Standing[]; scorers: PlayerStatistic[]; queries: Record<string, { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }>; organizationId: number; leagueId: number; seasonId: number }) {
  const recent = matches.filter((match) => match.status === 'FINISHED').slice(-5).reverse()
  return <div className="dashboard-grid"><DashboardCard title="Next matches" link={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)} query={queries.fixtures}>{fixtures.slice(0, 5).map((fixture) => <FixtureRow key={fixture.id} fixture={fixture} match={matches.find((item) => item.fixture_id === fixture.id)} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} />)}</DashboardCard><DashboardCard title="Recent results" link={dashboardPath(leagueId, 'fixtures', organizationId, seasonId)} query={queries.matches}>{recent.length === 0 ? <p className="muted">No finished matches yet.</p> : recent.map((match) => <MatchRow key={match.id} match={match} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} />)}</DashboardCard><DashboardCard title="Standings" link={dashboardPath(leagueId, 'table', organizationId, seasonId)} query={queries.standings}>{standings.slice(0, 5).length === 0 ? <p className="muted">No standings yet.</p> : <MiniTable rows={standings.slice(0, 5)} />}</DashboardCard><DashboardCard title="Top scorers" link={dashboardPath(leagueId, 'statistics', organizationId, seasonId)} query={queries.topScorers}>{scorers.length === 0 ? <p className="muted">No player statistics yet.</p> : <div className="rank-list">{scorers.slice(0, 5).map((player, index) => <div className="rank-row" key={player.id}><span>{index + 1}</span><strong>{player.full_name}</strong><b>{player.goals}</b></div>)}</div>}</DashboardCard></div>
}

function FixturesView({ fixtures, matches, query, organizationId, leagueId, seasonId }: { fixtures: Fixture[]; matches: Match[]; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }; organizationId: number; leagueId: number; seasonId: number }) {
  return <DashboardSection title="Fixtures" description="The season schedule and available match results." query={query}>{fixtures.length === 0 ? <EmptyCard title="No fixtures yet" text="Generate a fixture schedule from the organization management view." /> : <div className="fixture-list">{fixtures.map((fixture) => <FixtureRow key={fixture.id} fixture={fixture} match={matches.find((item) => item.fixture_id === fixture.id)} organizationId={organizationId} leagueId={leagueId} seasonId={seasonId} />)}</div>}</DashboardSection>
}

function StandingsView({ standings, query }: { standings: Standing[]; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown } }) {
  return <DashboardSection title="Standings" description="Finished matches, ordered by points and goal difference." query={query}>{standings.length === 0 ? <EmptyCard title="No standings yet" text="Standings appear after finished matches are recorded." /> : <div className="table-wrap"><table className="data-table"><thead><tr><th>#</th><th>Team</th><th>MP</th><th>W</th><th>D</th><th>L</th><th>GD</th><th>PTS</th></tr></thead><tbody>{standings.map((row, index) => <tr key={row.team_id}><td>{index + 1}</td><th>{row.team_name}</th><td>{row.mp}</td><td>{row.wins}</td><td>{row.draws}</td><td>{row.losses}</td><td>{row.gd}</td><td><strong>{row.pts}</strong></td></tr>)}</tbody></table></div>}</DashboardSection>
}

function TeamsView({ teams, query }: { teams: { id: number; team_name: string }[]; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown } }) {
  return <DashboardSection title="Season teams" description="Teams registered for this season." query={query}>{teams.length === 0 ? <EmptyCard title="No teams registered" text="Add teams to the season from the organization management view." /> : <div className="team-grid">{teams.map((team) => <div className="team-tile" key={team.id}><span className="org-avatar">{team.team_name.slice(0, 1).toUpperCase()}</span><strong>{team.team_name}</strong></div>)}</div>}</DashboardSection>
}

function StatisticsView({ statistics, topScorers, statisticsQuery, scorersQuery }: { statistics: PlayerStatistic[]; topScorers: PlayerStatistic[]; statisticsQuery: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }; scorersQuery: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown } }) {
  return <div className="dashboard-grid"><DashboardSection title="Top scorers" description="The leading goalscorers in this season." query={scorersQuery}>{topScorers.length === 0 ? <EmptyCard title="No scorers yet" text="Player statistics appear after goals are recorded." /> : <div className="rank-list">{topScorers.map((player, index) => <div className="rank-row" key={player.id}><span>{index + 1}</span><strong>{player.full_name}</strong><b>{player.goals} goals</b></div>)}</div>}</DashboardSection><DashboardSection title="Player statistics" description="Goals and cards for every player with activity." query={statisticsQuery}>{statistics.length === 0 ? <EmptyCard title="No statistics yet" text="Statistics appear after match events are recorded." /> : <div className="stat-list">{statistics.map((player) => <div className="list-item" key={player.id}><strong>{player.full_name}</strong><span className="item-meta">{player.goals} goals · {player.yellow_cards} yellow · {player.red_cards} red</span></div>)}</div>}</DashboardSection></div>
}

function DashboardSection({ title, description, query, children }: { title: string; description: string; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }; children: ReactNode }) { if (query.isPending) return <LoadingState label={`Loading ${title.toLowerCase()}…`} />; if (query.isError) return <ErrorState error={query.error} retry={() => void query.refetch()} />; return <section className="management-section dashboard-section"><div className="section-header"><div><h2>{title}</h2><p className="muted">{description}</p></div></div>{children}</section> }
function DashboardCard({ title, link, query, children }: { title: string; link: string; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown }; children: ReactNode }) { return <DashboardSection title={title} description="" query={query}><div className="card-heading"><Link className="text-link" to={link}>View all →</Link></div>{children}</DashboardSection> }
function FixtureRow({ fixture, match, organizationId, leagueId, seasonId }: { fixture: Fixture; match?: Match; organizationId: number; leagueId: number; seasonId: number }) { const content = <div className="fixture-row"><span className="round-label">R{fixture.round_number}</span><div><strong>{fixture.home_team_name}</strong><span className="versus">vs</span><strong>{fixture.away_team_name}</strong><span className="item-meta">{fixture.scheduled_at ? formatDate(fixture.scheduled_at) : 'Date to be confirmed'}</span></div>{match ? <span className="score-badge">{match.home_score} – {match.away_score}</span> : <span className="status-badge">Scheduled</span>}</div>; return match ? <Link className="fixture-link" to={`/matches/${match.id}?organization=${organizationId}&league=${leagueId}&season=${seasonId}`}>{content}</Link> : content }
function MatchRow({ match, organizationId, leagueId, seasonId }: { match: Match; organizationId: number; leagueId: number; seasonId: number }) { return <Link className="fixture-link" to={`/matches/${match.id}?organization=${organizationId}&league=${leagueId}&season=${seasonId}`}><div className="fixture-row"><span className="round-label">{match.status === 'LIVE' ? 'LIVE' : 'FT'}</span><div><strong>{match.home_team_name}</strong><span className="versus">vs</span><strong>{match.away_team_name}</strong></div><span className="score-badge">{match.home_score} – {match.away_score}</span></div></Link> }
function MiniTable({ rows }: { rows: Standing[] }) { return <div className="mini-table">{rows.map((row, index) => <div className="mini-row" key={row.team_id}><span>{index + 1}</span><strong>{row.team_name}</strong><b>{row.pts} pts</b></div>)}</div> }
function EmptyCard({ title, text }: { title: string; text: string }) { return <section className="empty-card"><h2>{title}</h2><p className="muted">{text}</p></section> }
function EventTimeline({ events, query }: { events: MatchEvent[]; query: { isPending: boolean; isError: boolean; error: unknown; refetch: () => unknown } }) { return <DashboardSection title="Match events" description="Goals, cards, and substitutions arrive here without refreshing." query={query}>{events.length === 0 ? <EmptyCard title="No events yet" text="Events will appear when the match is live." /> : <div className="event-list">{events.map((event) => <div className="event-row" key={event.id}><strong>{event.minute}'</strong><span>{event.event_type.replace('_', ' ').toLowerCase()}</span><span className="item-id">Player #{event.player_id}</span></div>)}</div>}</DashboardSection> }
function getDashboardView(pathname: string): DashboardView { const segment = pathname.split('/').filter(Boolean).pop(); return segment === 'fixtures' || segment === 'table' || segment === 'teams' || segment === 'statistics' ? segment : 'overview' }
function dashboardPath(leagueId: number, view: DashboardView, organizationId: number, seasonId?: number) { const suffix = view === 'overview' ? '' : `/${view}`; const season = seasonId ? `&season=${seasonId}` : ''; return `/leagues/${leagueId}${suffix}?organization=${organizationId}${season}` }
function formatDate(value: string) { return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) }
