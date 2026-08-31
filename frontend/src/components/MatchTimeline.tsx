import type { MatchEvent } from '../lib/api'
import { cn } from '../lib/utils'

/**
 * Events on a vertical minute axis with the two clubs on opposite sides, the way
 * a matchday programme prints them. Yellow and red appear here and nowhere else
 * in the product.
 */
type MatchTimelineProps = {
  events: MatchEvent[]
  homeTeamId: number
  homeTeamName: string
  awayTeamName: string
  playerNames: Map<number, string>
}

export function MatchTimeline({ events, homeTeamId, homeTeamName, awayTeamName, playerNames }: MatchTimelineProps) {
  const ordered = [...events].sort((a, b) => a.minute - b.minute || a.id - b.id)

  return (
    <div>
      <div className="grid grid-cols-[1fr_2.5rem_1fr] items-baseline border-b border-chalk pb-1.5">
        <p className="truncate text-right font-condensed text-sm font-semibold text-ink">{homeTeamName}</p>
        <p className="text-center font-condensed text-2xs text-ink-muted">Min</p>
        <p className="truncate font-condensed text-sm font-semibold text-ink">{awayTeamName}</p>
      </div>
      <ol className="m-0 list-none p-0">
        {ordered.map((event) => {
          const atHome = event.team_id === homeTeamId
          return (
            <li key={event.id} className="grid grid-cols-[1fr_2.5rem_1fr] items-center">
              <div className={cn('py-2', atHome ? 'flex justify-end' : 'invisible')}>
                {atHome && <EventDetail event={event} playerNames={playerNames} align="right" />}
              </div>
              {/* The axis: a continuous rule with the minute set on it. */}
              <div className="relative flex h-full min-h-11 items-center justify-center">
                <span className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-chalk" aria-hidden="true" />
                <span className="tabular relative bg-paper-raised px-1 py-0.5 font-condensed text-2xs font-semibold text-ink-muted">
                  {event.minute}&apos;
                </span>
              </div>
              <div className={cn('py-2', atHome ? 'invisible' : 'flex justify-start')}>
                {!atHome && <EventDetail event={event} playerNames={playerNames} align="left" />}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

function EventDetail({ event, playerNames, align }: { event: MatchEvent; playerNames: Map<number, string>; align: 'left' | 'right' }) {
  const name = playerNames.get(event.player_id) ?? `Player #${event.player_id}`
  return (
    <span
      className={cn(
        'flex items-center gap-2',
        align === 'right' ? 'flex-row-reverse text-right' : 'text-left',
      )}
    >
      <EventMark type={event.event_type} />
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium text-ink">{name}</span>
        <span className="block text-2xs text-ink-muted">{eventLabel(event.event_type)}</span>
      </span>
    </span>
  )
}

function EventMark({ type }: { type: string }) {
  if (type === 'GOAL') {
    return (
      <span
        className="grid size-5 shrink-0 place-items-center rounded-full border-2 border-ink"
        aria-hidden="true"
      >
        <span className="size-1.5 rounded-full bg-ink" />
      </span>
    )
  }
  if (type === 'YELLOW_CARD') {
    return <span className="h-5 w-3.5 shrink-0 rounded-[1px] bg-booking" aria-hidden="true" />
  }
  if (type === 'RED_CARD') {
    return <span className="h-5 w-3.5 shrink-0 rounded-[1px] bg-sending-off" aria-hidden="true" />
  }
  return (
    <span className="grid size-5 shrink-0 place-items-center text-ink-muted" aria-hidden="true">
      <svg viewBox="0 0 16 16" className="size-4" fill="none" stroke="currentColor" strokeWidth="1.6">
        <path d="M2 5h8l-2.5-2.5M14 11H6l2.5 2.5" />
      </svg>
    </span>
  )
}

function eventLabel(type: string) {
  if (type === 'GOAL') return 'Goal'
  if (type === 'YELLOW_CARD') return 'Yellow card'
  if (type === 'RED_CARD') return 'Red card'
  if (type === 'SUBSTITUTION') return 'Substitution'
  return type.replace(/_/g, ' ').toLowerCase()
}
