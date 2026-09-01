import { FormGuide } from './FormGuide'
import { TeamCrest } from './TeamCrest'
import { teamForm } from '../lib/form'
import type { Match, Standing } from '../lib/api'
import { cn } from '../lib/utils'

/**
 * The league table, typeset rather than boxed: hairline column rules, a position
 * gutter, tabular figures, and zones marked with a bar in the margin the way a
 * newspaper marks them. Row background tints are deliberately not used — they
 * would fight the form-guide marks sitting in the same row.
 */
type StandingsTableProps = {
  standings: Standing[]
  matches: Match[]
  /** Rows in the promotion zone at the top. */
  promotion?: number
  /** Rows in the relegation zone at the bottom. */
  relegation?: number
}

const NUM = 'px-2 py-2 text-right tabular-nums'
const HEAD = 'px-2 py-1.5 text-right font-condensed text-2xs font-semibold uppercase tracking-[0.06em] text-ink-muted'

export function StandingsTable({ standings, matches, promotion = 3, relegation = 2 }: StandingsTableProps) {
  // Zones only make sense once the division is big enough to have them.
  const zoned = standings.length >= 8
  const promotionCut = zoned ? promotion : 0
  const relegationCut = zoned ? standings.length - relegation : standings.length

  return (
    <figure className="m-0">
      <div className="relative overflow-x-auto rounded-[var(--radius-card)] border border-chalk bg-paper-raised shadow-panel">
        <table className="w-full min-w-[42rem] border-collapse text-sm">
          <caption className="sr-only">
            League standings: position, club, matches played, wins, draws, losses, goals for,
            goals against, goal difference, points, and form over the last five matches.
          </caption>
          <thead>
            <tr className="border-b-2 border-ink">
              <th scope="col" className={cn(HEAD, 'sticky left-0 z-10 bg-paper-raised text-left')}>
                Club
              </th>
              <th scope="col" className={HEAD} title="Matches played">MP</th>
              <th scope="col" className={HEAD} title="Won">W</th>
              <th scope="col" className={HEAD} title="Drawn">D</th>
              <th scope="col" className={HEAD} title="Lost">L</th>
              <th scope="col" className={cn(HEAD, 'hidden sm:table-cell')} title="Goals for">GF</th>
              <th scope="col" className={cn(HEAD, 'hidden sm:table-cell')} title="Goals against">GA</th>
              <th scope="col" className={HEAD} title="Goal difference">GD</th>
              <th scope="col" className={cn(HEAD, 'hidden text-left sm:table-cell')}>Form</th>
              <th scope="col" className={cn(HEAD, 'sticky right-0 z-10 border-l border-chalk bg-paper-raised text-ink')} title="Points">
                Pts
              </th>
            </tr>
          </thead>
          <tbody>
            {standings.map((row, index) => {
              const position = index + 1
              const inPromotion = index < promotionCut
              const inRelegation = index >= relegationCut
              return (
                <tr
                  key={row.team_id}
                  className={cn(
                    'group border-b border-chalk last:border-b-0',
                    index === promotionCut - 1 && 'border-b-2 border-b-ink',
                    index === relegationCut && 'border-t-2 border-t-ink',
                    'transition-colors hover:bg-pitch-wash/60',
                  )}
                >
                  <th
                    scope="row"
                    className={cn(
                      'sticky left-0 z-10 bg-paper-raised py-2 pr-3 text-left font-normal transition-colors group-hover:bg-pitch-wash/60',
                      // The zone marker is a bar in the margin, not a row tint.
                      inPromotion && 'border-l-[3px] border-l-pitch',
                      inRelegation && 'border-l-[3px] border-l-ink',
                      !inPromotion && !inRelegation && 'border-l-[3px] border-l-transparent',
                    )}
                  >
                    <span className="flex items-center gap-2.5 pl-2">
                      <span className="tabular w-5 shrink-0 text-right font-condensed text-sm font-semibold text-ink-muted">
                        {position}
                      </span>
                      <TeamCrest name={row.team_name} size="sm" />
                      <span className="min-w-0 truncate font-condensed text-base font-semibold text-ink">
                        {row.team_name}
                      </span>
                    </span>
                  </th>
                  <td className={NUM}>{row.mp}</td>
                  <td className={NUM}>{row.wins}</td>
                  <td className={NUM}>{row.draws}</td>
                  <td className={NUM}>{row.losses}</td>
                  <td className={cn(NUM, 'hidden sm:table-cell text-ink-muted')}>{row.gf}</td>
                  <td className={cn(NUM, 'hidden sm:table-cell text-ink-muted')}>{row.ga}</td>
                  <td className={NUM}>{row.gd > 0 ? `+${row.gd}` : row.gd}</td>
                  <td className="hidden py-2 pl-2 pr-3 sm:table-cell">
                    <FormGuide form={teamForm(matches, row.team_id)} />
                  </td>
                  <td className={cn(NUM, 'sticky right-0 z-10 border-l border-chalk bg-paper-raised font-condensed text-base font-bold transition-colors group-hover:bg-pitch-wash/60')}>
                    {row.pts}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {zoned && (
        <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-ink-muted">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-[3px] bg-pitch" aria-hidden="true" />
            Promotion
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-[3px] bg-ink" aria-hidden="true" />
            Relegation
          </span>
          <span>Form runs oldest to most recent.</span>
        </figcaption>
      )}
    </figure>
  )
}
