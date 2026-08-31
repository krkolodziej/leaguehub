import type { ReactNode } from 'react'

type PageHeadingProps = {
  title: string
  subtitle?: string
  /** A short right-aligned fact, e.g. a count. */
  meta?: string
  children?: ReactNode
}

export function PageHeading({ title, subtitle, meta, children }: PageHeadingProps) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-x-6 gap-y-3 border-b-2 border-ink pb-3">
      <div className="min-w-0">
        <h1 className="text-xl leading-tight">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-ink-muted">{subtitle}</p>}
      </div>
      {meta && (
        <p className="tabular font-condensed text-sm font-semibold text-ink-muted">{meta}</p>
      )}
      {children}
    </div>
  )
}
