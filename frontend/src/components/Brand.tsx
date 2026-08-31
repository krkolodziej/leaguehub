import { Link } from 'react-router-dom'

import { cn } from '../lib/utils'

/**
 * The mark is a pitch: a green rectangle with a chalk halfway line and centre
 * circle. Drawn rather than lettered, so it reads at 24px on a phone header.
 */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 20" className={cn('h-5 w-7', className)} aria-hidden="true">
      <rect width="28" height="20" fill="var(--color-pitch)" />
      <g stroke="#fff" strokeWidth="1" fill="none" opacity="0.9">
        <path d="M14 0.5V19.5" />
        <circle cx="14" cy="10" r="3.6" />
        <path d="M0.5 6.2H4.4V13.8H0.5" />
        <path d="M27.5 6.2H23.6V13.8H27.5" />
      </g>
    </svg>
  )
}

export function Brand({ to = '/dashboard', className }: { to?: string; className?: string }) {
  return (
    <Link
      to={to}
      className={cn(
        'inline-flex items-center gap-2 font-condensed text-lg font-bold tracking-tight text-ink',
        className,
      )}
    >
      <BrandMark />
      LeagueHub
    </Link>
  )
}
