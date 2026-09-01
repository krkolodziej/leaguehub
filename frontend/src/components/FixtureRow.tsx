import { Link } from 'react-router-dom'

import { MatchStatus } from './MatchStatus'
import { ScoreChip } from './ScoreLine'
import { formatKickoff } from '../lib/datetime'
import { TeamCrest } from './TeamCrest'
import type { Match } from '../lib/api'

type FixtureRowProps = {
  /** Omitted for a bare result, where the round is not part of the caption. */
  round?: number
  homeTeam: string
  awayTeam: string
  kickoff: string | null
  match?: Match
  href?: string
}

/**
 * The newspaper fixture format: home reads inward to the score, away reads
 * outward from it, with the round and the state as caption underneath.
 */
export function FixtureRow({ round, homeTeam, awayTeam, kickoff, match, href }: FixtureRowProps) {
  const played = match ? match.status === 'FINISHED' || match.status === 'LIVE' : false
  const body = (
    <div className="px-3 py-3">
      <div className="flex items-center gap-2 sm:gap-3">
        <span className="tabular hidden w-8 shrink-0 font-condensed text-2xs font-semibold text-ink-muted sm:inline">
          {round ? `R${round}` : ''}
        </span>
        <span className="flex min-w-0 flex-1 items-center justify-end gap-2">
          <span className="min-w-0 truncate text-right font-condensed text-base font-semibold text-ink">
            {homeTeam}
          </span>
          <TeamCrest name={homeTeam} size="sm" />
        </span>
        <ScoreChip
          homeScore={match?.home_score ?? 0}
          awayScore={match?.away_score ?? 0}
          played={played}
          className="w-12 shrink-0 text-center sm:w-16"
        />
        <span className="flex min-w-0 flex-1 items-center gap-2">
          <TeamCrest name={awayTeam} size="sm" />
          <span className="min-w-0 truncate font-condensed text-base font-semibold text-ink">{awayTeam}</span>
        </span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 pl-0 sm:pl-11">
        <MatchStatus status={match?.status ?? 'SCHEDULED'} />
        {round ? <span className="tabular text-xs text-ink-muted sm:hidden">Round {round}</span> : null}
        {kickoff && (
          <span className="tabular ml-auto text-xs text-ink-muted">{formatKickoff(kickoff)}</span>
        )}
      </div>
    </div>
  )

  if (!href) return body
  return (
    <Link
      className="block transition-colors duration-150 hover:bg-pitch-wash focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-pitch/40"
      to={href}
    >
      {body}
    </Link>
  )
}
