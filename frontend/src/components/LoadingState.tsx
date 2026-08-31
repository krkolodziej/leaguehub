import { Skeleton } from './ui/skeleton'

type LoadingStateProps = { label?: string; rows?: number }

export function LoadingState({ label = 'Loading…', rows = 4 }: LoadingStateProps) {
  return (
    <div className="py-2" role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      <div className="space-y-2" aria-hidden="true">
        {Array.from({ length: rows }, (_, index) => (
          <Skeleton key={index} className="h-11 w-full" />
        ))}
      </div>
    </div>
  )
}
