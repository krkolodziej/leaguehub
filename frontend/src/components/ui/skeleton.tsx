import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

export function Skeleton({ className, ...props }: ComponentProps<'div'>) {
  // Deliberately static: a live match is the only thing in the product that moves.
  return <div className={cn('rounded-[2px] bg-ink/8', className)} {...props} />
}
