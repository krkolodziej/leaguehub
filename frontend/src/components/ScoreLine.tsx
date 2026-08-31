import { TeamCrest } from './TeamCrest'
import { formatKickoff } from '../lib/datetime'
import { cn } from '../lib/utils'

type ScoreLineProps = {
  homeTeam: string
  awayTeam: string
  homeScore: number
  awayScore: number
  /** Scores only mean something once a ball has been kicked. */
  played: boolean
  kickoff?: string | null
}

/**
 * The score is the largest thing on the page, because it is the single fact a
 * reader came for. Everything around it is caption.
 */
export function ScoreLine({ homeTeam, awayTeam, homeScore, awayScore, played, kickoff }: ScoreLineProps) {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 sm:gap-6">
      <div className="flex min-w-0 flex-col items-center gap-2 sm:flex-row sm:justify-end">
        <TeamCrest name={homeTeam} size="xl" className="sm:order-2" />
        <span className="font-condensed text-lg font-semibold leading-tight text-ink sm:order-1 sm:text-right sm:text-xl">
          {homeTeam}
        </span>
      </div>
      <div className="text-center">
        {played ? (
          <p className="tabular m-0 font-condensed text-2xl font-bold leading-none text-ink sm:text-[length:var(--text-score)]">
            {homeScore}
            <span className="px-1 text-ink-muted sm:px-2">:</span>
            {awayScore}
          </p>
        ) : (
          <p className="m-0 font-condensed text-2xl font-bold leading-none text-ink-muted">
            <span aria-hidden="true">–</span>
            <span className="sr-only">Not played yet</span>
          </p>
        )}
        {kickoff && (
          <p className="tabular mt-2 text-xs text-ink-muted">{formatKickoff(kickoff)}</p>
        )}
      </div>
      <div className="flex min-w-0 flex-col items-center gap-2 sm:flex-row sm:justify-start">
        <TeamCrest name={awayTeam} size="xl" />
        <span className="font-condensed text-lg font-semibold leading-tight text-ink sm:text-left sm:text-xl">
          {awayTeam}
        </span>
      </div>
    </div>
  )
}

/** A compact score for lists, where the score still outweighs the team names. */
export function ScoreChip({ homeScore, awayScore, played, className }: { homeScore: number; awayScore: number; played: boolean; className?: string }) {
  if (!played) {
    return (
      <span className={cn('tabular font-condensed text-lg font-semibold text-ink-muted', className)}>
        <span aria-hidden="true">–</span>
        <span className="sr-only">Not played yet</span>
      </span>
    )
  }
  return (
    <span className={cn('tabular whitespace-nowrap font-condensed text-2xl font-bold leading-none text-ink', className)}>
      {homeScore}
      <span className="px-1 text-ink-muted">:</span>
      {awayScore}
    </span>
  )
}
