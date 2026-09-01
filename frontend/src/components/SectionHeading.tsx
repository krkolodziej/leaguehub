import type { ReactNode } from 'react'

type SectionHeadingProps = {
  title: string
  description?: string
  /** A short right-aligned fact, usually a count. */
  count?: number
  /** Right-aligned controls or a "view all" link. */
  children?: ReactNode
}

/**
 * The rule under a section title. Every section on every page uses this, so the
 * horizontal rules across a page land on the same rhythm.
 */
export function SectionHeading({ title, description, count, children }: SectionHeadingProps) {
  return (
    <div className="mb-3 flex flex-wrap items-end justify-between gap-x-4 gap-y-1 border-b border-chalk pb-2">
      <div className="min-w-0">
        <h2 className="text-lg leading-tight">{title}</h2>
        {description && <p className="mt-0.5 text-sm text-ink-muted">{description}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-3">
        {children}
        {count !== undefined && (
          <span className="tabular rounded-[var(--radius-control)] bg-ink/[0.06] px-1.5 py-0.5 font-condensed text-2xs font-bold text-ink-muted">
            {count}
          </span>
        )}
      </div>
    </div>
  )
}
