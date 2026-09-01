import type { ReactNode } from 'react'

type EmptyStateProps = {
  title: string
  /** Say what to do next. Never just "no data". */
  action: string
  children?: ReactNode
}

export function EmptyState({ title, action, children }: EmptyStateProps) {
  return (
    <div className="rounded-[var(--radius-card)] border border-dashed border-chalk bg-paper-raised px-5 py-9 text-center">
      <h3 className="font-condensed text-lg text-ink">{title}</h3>
      <p className="mx-auto mt-1.5 max-w-[46ch] text-sm text-ink-muted">{action}</p>
      {children && <div className="mt-4 flex justify-center">{children}</div>}
    </div>
  )
}
