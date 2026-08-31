import { ChevronLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

export function BackLink({ to, children }: { to: string; children: string }) {
  return (
    <Link
      className="mb-4 inline-flex items-center gap-1 text-sm font-medium text-ink-muted hover:text-ink"
      to={to}
    >
      <ChevronLeft className="size-4" aria-hidden="true" />
      {children}
    </Link>
  )
}
