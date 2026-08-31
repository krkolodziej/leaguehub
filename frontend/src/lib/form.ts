import type { Match } from './api'

export type FormResult = 'W' | 'D' | 'L'

/** The last five results for a team, oldest first, as a printed table prints them. */
export function teamForm(matches: Match[], teamId: number, limit = 5): FormResult[] {
  return matches
    .filter(
      (match) =>
        match.status === 'FINISHED' &&
        (match.home_team_id === teamId || match.away_team_id === teamId),
    )
    .sort((a, b) => (a.finished_at ?? '').localeCompare(b.finished_at ?? ''))
    .slice(-limit)
    .map((match) => {
      const atHome = match.home_team_id === teamId
      const scored = atHome ? match.home_score : match.away_score
      const conceded = atHome ? match.away_score : match.home_score
      if (scored > conceded) return 'W'
      if (scored < conceded) return 'L'
      return 'D'
    })
}
