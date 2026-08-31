import { cn } from '../lib/utils'
import type { FormResult } from '../lib/form'

const MARK: Record<FormResult, string> = {
  W: 'bg-pitch text-white',
  D: 'bg-chalk text-ink',
  L: 'bg-ink text-paper',
}

const LABEL: Record<FormResult, string> = { W: 'won', D: 'drew', L: 'lost' }

/** Five compact marks. Letters carry the meaning so colour is never load bearing. */
export function FormGuide({ form, className }: { form: FormResult[]; className?: string }) {
  if (form.length === 0) return <span className="text-2xs text-ink-muted">—</span>
  return (
    <span className={cn('inline-flex gap-[3px]', className)}>
      {form.map((result, index) => (
        <span
          key={index}
          className={cn(
            'grid size-4 place-items-center rounded-[1px] font-condensed text-[0.6rem] font-bold',
            MARK[result],
          )}
          title={LABEL[result]}
        >
          {result}
        </span>
      ))}
      <span className="sr-only">{form.map((result) => LABEL[result]).join(', ')}</span>
    </span>
  )
}
