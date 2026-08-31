import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { LeagueForm, PlayerForm, RosterForm, SeasonForm, SeasonTeamForm, TeamForm } from '../components/ManagementForms'
import { useOrganizations } from '../lib/organizations'
import { useLeagues, usePlayers, useRoster, useSeasonTeams, useSeasons, useTeams } from '../lib/management'

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
  if (!organization) return <ErrorState error={new Error('Organization not found or you do not have access.')} />

  return (
    <div className="management-page">
      <Link className="back-link" to="/dashboard">← Back to dashboard</Link>
      <div className="page-heading"><div><p className="eyebrow">Organization</p><h1>{organization.name}</h1><p className="muted">/{organization.slug} · your role: {organization.my_role?.toLowerCase()}</p></div>{canManage && <span className="manager-pill">Manager access</span>}</div>
      <section className="management-section"><SectionHeader title="Leagues" description="Competitions in this organization." count={leagues.data?.length} />{leagues.isPending ? <LoadingState label="Loading leagues…" /> : leagues.isError ? <ErrorState error={leagues.error} retry={() => void leagues.refetch()} /> : <div className="item-list">{leagues.data.length === 0 ? <p className="muted">No leagues yet.</p> : leagues.data.map((league) => <div className="list-item" key={league.id}><div><strong>{league.name}</strong><span className="item-meta">/{league.slug}</span></div><Link className="text-link" to={`/leagues/${league.id}?organization=${id}`}>Open dashboard →</Link></div>)}</div>}{canManage && <LeagueForm organizationId={id} />}</section>
      <section className="management-section"><SectionHeader title="Seasons" description="Choose a league to manage its seasons." count={seasons.data?.length} />{leagues.data && leagues.data.length > 0 && <select className="select-control" value={selectedLeagueId ?? ''} onChange={(event) => { setLeagueId(Number(event.target.value)); setSeasonId(undefined); setSeasonTeamId(undefined) }}><option value="">Choose league…</option>{leagues.data.map((league) => <option key={league.id} value={league.id}>{league.name}</option>)}</select>}{seasons.isPending ? <LoadingState label="Loading seasons…" /> : seasons.isError ? <ErrorState error={seasons.error} retry={() => void seasons.refetch()} /> : <div className="item-list">{(seasons.data ?? []).length === 0 ? <p className="muted">No seasons for this league yet.</p> : seasons.data.map((season) => <div className="list-item" key={season.id}><div><strong>{season.name}</strong><span className="item-meta">{season.start_date}{season.end_date && ` → ${season.end_date}`}</span></div><button className="select-link" onClick={() => { setSeasonId(season.id); setSeasonTeamId(undefined) }}>{selectedSeasonId === season.id ? 'Selected' : 'Select'}</button></div>)}</div>}{canManage && selectedLeagueId && <SeasonForm organizationId={id} leagueId={selectedLeagueId} />}</section>
      <div className="management-grid"><section className="management-section"><SectionHeader title="Teams" description="Organization-wide teams." count={teams.data?.length} />{teams.isPending ? <LoadingState label="Loading teams…" /> : teams.isError ? <ErrorState error={teams.error} retry={() => void teams.refetch()} /> : <ItemNames items={teams.data ?? []} empty="No teams yet." />}{canManage && <TeamForm organizationId={id} />}</section><section className="management-section"><SectionHeader title="Players" description="Players available to rosters." count={players.data?.length} />{players.isPending ? <LoadingState label="Loading players…" /> : players.isError ? <ErrorState error={players.error} retry={() => void players.refetch()} /> : <ItemNames items={(players.data ?? []).map((player) => ({ id: player.id, name: player.full_name }))} empty="No players yet." />}{canManage && <PlayerForm organizationId={id} />}</section></div>
      <section className="management-section"><SectionHeader title="Season rosters" description="Attach teams to a season, then add its players." count={seasonTeams.data?.length} />{selectedLeagueId && selectedSeasonId && <div className="selection-row"><select className="select-control" value={selectedSeasonId} onChange={(event) => { setSeasonId(Number(event.target.value)); setSeasonTeamId(undefined) }}>{(seasons.data ?? []).map((season) => <option key={season.id} value={season.id}>{season.name}</option>)}</select><select className="select-control" value={selectedSeasonTeamId ?? ''} onChange={(event) => setSeasonTeamId(Number(event.target.value))}><option value="">Choose seasonal team…</option>{(seasonTeams.data ?? []).map((item) => <option key={item.id} value={item.id}>{item.team_name}</option>)}</select></div>}{canManage && selectedLeagueId && selectedSeasonId && availableTeams.length > 0 && <SeasonTeamForm organizationId={id} leagueId={selectedLeagueId} seasonId={selectedSeasonId} teams={availableTeams} />}{selectedSeasonTeamId && <div className="roster-area">{roster.isPending ? <LoadingState label="Loading roster…" /> : roster.isError ? <ErrorState error={roster.error} retry={() => void roster.refetch()} /> : <ItemNames items={(roster.data ?? []).map((entry) => ({ id: entry.id, name: `${entry.player_name}${entry.shirt_number ? ` · #${entry.shirt_number}` : ''}${entry.is_captain ? ' · captain' : ''}` }))} empty="No roster players yet." />}{canManage && selectedLeagueId && selectedSeasonId && <RosterForm organizationId={id} leagueId={selectedLeagueId} seasonId={selectedSeasonId} seasonTeamId={selectedSeasonTeamId} players={(players.data ?? []).map((player) => ({ id: player.id, full_name: player.full_name }))} />}</div>}</section>
    </div>
  )
}

function SectionHeader({ title, description, count }: { title: string; description: string; count?: number }) { return <div className="section-header"><div><h2>{title}</h2><p className="muted">{description}</p></div>{count !== undefined && <span className="count-pill">{count}</span>}</div> }
function ItemNames({ items, empty }: { items: { id: number; name: string }[]; empty: string }) { return <div className="item-list">{items.length === 0 ? <p className="muted">{empty}</p> : items.map((item) => <div className="list-item" key={item.id}><strong>{item.name}</strong><span className="item-id">#{item.id}</span></div>)}</div> }
