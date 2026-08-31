import { errorMessage } from '../lib/errors'
import { Button } from './ui/button'

type ErrorStateProps = { error: unknown; retry?: () => void }

/**
 * Failures are set in ink behind a heavy rule. Red belongs to red cards.
 */
export function ErrorState({ error, retry }: ErrorStateProps) {
  return (
    <div className="border-l-[3px] border-ink bg-paper-raised px-4 py-3" role="alert">
      <p className="font-condensed text-sm font-semibold uppercase tracking-[0.08em] text-ink">
        That did not work
      </p>
      <p className="mt-1 text-sm text-ink-muted">{errorMessage(error)}</p>
      {retry && (
        <Button className="mt-3" variant="outline" size="sm" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  )
}
