import { cn } from '../lib/utils'

/**
 * Five statuses, five structurally different treatments. Colour alone is never
 * the signal: LIVE is the one moving element in the product, FINISHED is a solid
 * ink chip, SCHEDULED is a plain time, CANCELLED is struck through, POSTPONED is
 * ruled. The reserved card colours are deliberately absent.
 */
type MatchStatusProps = {
  status: string
  className?: string
}

const CHIP = 'inline-flex items-center gap-1.5 px-1.5 py-0.5 font-condensed text-2xs font-semibold uppercase tracking-[0.08em]'

export function MatchStatus({ status, className }: MatchStatusProps) {
  if (status === 'LIVE') {
    return (
      <span className={cn(CHIP, 'bg-pitch text-white', className)}>
        <span className="animate-live inline-block size-1.5 rounded-full bg-white" aria-hidden="true" />
        Live
      </span>
    )
  }
  if (status === 'FINISHED') {
    return <span className={cn(CHIP, 'bg-ink text-paper', className)}>Full time</span>
  }
  if (status === 'CANCELLED') {
    return (
      <span className={cn(CHIP, 'text-ink-muted line-through decoration-2', className)}>
        Cancelled
      </span>
    )
  }
  if (status === 'POSTPONED') {
    return (
      <span className={cn(CHIP, 'border-l-[3px] border-ink pl-2 text-ink', className)}>
        Postponed
      </span>
    )
  }
  return (
    <span className={cn(CHIP, 'border border-chalk text-ink-muted', className)}>Scheduled</span>
  )
}
