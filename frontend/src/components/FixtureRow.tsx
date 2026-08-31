import { Link } from 'react-router-dom'

import { MatchStatus } from './MatchStatus'
import { ScoreChip } from './ScoreLine'
import { formatKickoff } from '../lib/datetime'
import { TeamCrest } from './TeamCrest'
import type { Match } from '../lib/api'

type FixtureRowProps = {
  round: number
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
    <div className="px-3 py-2.5">
      <div className="flex items-center gap-2 sm:gap-3">
        <span className="tabular hidden w-8 shrink-0 font-condensed text-2xs font-semibold text-ink-muted sm:inline">
          R{round}
        </span>
        <span className="flex min-w-0 flex-1 items-center justify-end gap-2">
          <span className="truncate text-right font-condensed text-base font-semibold text-ink">
            {homeTeam}
          </span>
          <TeamCrest name={homeTeam} size="sm" />
        </span>
        <ScoreChip
          homeScore={match?.home_score ?? 0}
          awayScore={match?.away_score ?? 0}
          played={played}
          className="w-16 shrink-0 text-center"
        />
        <span className="flex min-w-0 flex-1 items-center gap-2">
          <TeamCrest name={awayTeam} size="sm" />
          <span className="truncate font-condensed text-base font-semibold text-ink">{awayTeam}</span>
        </span>
      </div>
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-0 sm:pl-11">
        <MatchStatus status={match?.status ?? 'SCHEDULED'} />
        <span className="tabular text-xs text-ink-muted sm:hidden">Round {round}</span>
        {kickoff && <span className="tabular text-xs text-ink-muted">{formatKickoff(kickoff)}</span>}
      </div>
    </div>
  )

  if (!href) return body
  return (
    <Link className="block hover:bg-pitch-wash" to={href}>
      {body}
    </Link>
  )
}
