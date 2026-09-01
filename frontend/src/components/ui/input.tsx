import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

export function Input({ className, ...props }: ComponentProps<'input'>) {
  return (
    <input
      className={cn(
        'h-10 w-full rounded-[var(--radius-control)] border border-chalk bg-paper-raised px-3 text-base text-ink',
        'transition-[border-color,box-shadow] duration-150',
        'placeholder:text-ink-muted/70',
        'hover:border-ink-muted/50',
        // A ring rather than an outline: the box never shifts when it takes focus.
        'focus:border-pitch focus:outline-none focus:ring-2 focus:ring-pitch/25',
        'aria-[invalid=true]:border-ink aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-ink/15',
        'disabled:cursor-not-allowed disabled:bg-paper disabled:opacity-60',
        className,
      )}
      {...props}
    />
  )
}
