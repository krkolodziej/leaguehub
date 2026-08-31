import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

/**
 * A boxed surface. Reserved for things that genuinely are discrete objects —
 * match cards, form panels, crests — never as a wrapper around every section.
 */
export function Card({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('border border-chalk bg-paper-raised', className)} {...props} />
}

export function CardHeader({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('border-b border-chalk px-4 py-3', className)} {...props} />
}

export function CardTitle({ className, ...props }: ComponentProps<'h2'>) {
  return <h2 className={cn('font-condensed text-lg leading-tight', className)} {...props} />
}

export function CardContent({ className, ...props }: ComponentProps<'div'>) {
  return <div className={cn('px-4 py-3', className)} {...props} />
}
