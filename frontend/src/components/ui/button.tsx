import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import type { ComponentProps } from 'react'

import { cn } from '../../lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-colors disabled:pointer-events-none disabled:opacity-55 [&_svg]:pointer-events-none [&_svg]:shrink-0',
  {
    variants: {
      variant: {
        // Solid pitch green carries every primary action.
        primary: 'bg-pitch text-white hover:bg-pitch-dark',
        // A ruled outline, the way a printed form marks a secondary choice.
        outline: 'border border-ink/25 bg-transparent text-ink hover:border-ink hover:bg-ink/5',
        subtle: 'bg-pitch-wash text-pitch-dark hover:bg-pitch/15',
        ghost: 'text-ink-muted hover:bg-ink/5 hover:text-ink',
        link: 'text-pitch underline-offset-4 hover:underline',
      },
      size: {
        sm: 'h-8 rounded-[2px] px-3 text-xs',
        md: 'h-10 rounded-[2px] px-4 text-sm',
        lg: 'h-11 rounded-[2px] px-5 text-base',
        icon: 'size-9 rounded-[2px]',
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
