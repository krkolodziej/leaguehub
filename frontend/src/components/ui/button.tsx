import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

const buttonVariants = cva(
  [
    'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)]',
    'font-medium transition-[background-color,border-color,color,box-shadow,transform] duration-150',
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pitch/40 focus-visible:ring-offset-2 focus-visible:ring-offset-paper-raised',
    'active:translate-y-px disabled:pointer-events-none disabled:opacity-55',
    '[&_svg]:pointer-events-none [&_svg]:shrink-0',
  ].join(' '),
  {
    variants: {
      variant: {
        // Solid pitch green carries every primary action.
        primary: 'bg-pitch text-white shadow-panel hover:bg-pitch-dark',
        // A ruled outline, the way a printed form marks a secondary choice.
        outline: 'border border-ink/20 bg-paper-raised text-ink hover:border-ink/45 hover:bg-ink/[0.04]',
        subtle: 'bg-pitch-wash text-pitch-dark hover:bg-pitch/15',
        ghost: 'text-ink-muted hover:bg-ink/[0.06] hover:text-ink',
        link: 'text-pitch underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-11 px-5 text-base',
        icon: 'size-9',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

type ButtonProps = ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Comp = asChild ? Slot : 'button'
  return <Comp className={cn(buttonVariants({ variant, size }), className)} {...props} />
}
