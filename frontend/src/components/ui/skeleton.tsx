import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

export function Skeleton({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('animate-pulse rounded-[2px] bg-ink/8', className)} {...props} />
}
