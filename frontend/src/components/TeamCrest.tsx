import { cn } from '../lib/utils'
import { teamColor, teamInitials } from '../lib/teamColor'

const SIZES = {
  sm: 'size-6 text-[0.6rem]',
  md: 'size-8 text-2xs',
  lg: 'size-12 text-sm',
  xl: 'size-16 text-lg',
}

type TeamCrestProps = {
  name: string
  size?: keyof typeof SIZES
  className?: string
}

export function TeamCrest({ name, size = 'md', className }: TeamCrestProps) {
  return (
    <span
      className={cn(
        'inline-grid shrink-0 place-items-center rounded-full font-condensed font-bold tracking-tight text-white',
        SIZES[size],
        className,
      )}
      style={{ backgroundColor: teamColor(name) }}
      aria-hidden="true"
    >
      {teamInitials(name)}
    </span>
  )
}
