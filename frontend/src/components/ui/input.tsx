import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

export function Input({ className, ...props }: ComponentProps<'input'>) {
  return (
    <input
      className={cn(
        'h-10 w-full rounded-[2px] border border-chalk bg-paper-raised px-3 text-base text-ink',
        'placeholder:text-ink-muted/70',
        'focus-visible:border-pitch focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-pitch',
        'aria-[invalid=true]:border-ink aria-[invalid=true]:border-2',
        'disabled:cursor-not-allowed disabled:opacity-60',
        className,
      )}
      {...props}
    />
  )
}
