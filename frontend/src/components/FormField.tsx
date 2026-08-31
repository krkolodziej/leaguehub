import type { InputHTMLAttributes } from 'react'

import { Input } from './ui/input'
import { Label } from './ui/label'

type FormFieldProps = {
  id: string
  label: string
  error?: string
  hint?: string
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'id'>

/**
 * A labelled input whose error sits outside the label, so the message is
 * announced as a description rather than becoming part of the field name.
 */
export function FormField({ id, label, error, hint, ...inputProps }: FormFieldProps) {
  const description = error ? `${id}-error` : hint ? `${id}-hint` : undefined
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={description}
        {...inputProps}
      />
      {error && (
        <span className="text-xs font-medium text-ink" id={`${id}-error`}>
          {error}
        </span>
      )}
      {!error && hint && (
        <span className="text-xs text-ink-muted" id={`${id}-hint`}>
          {hint}
        </span>
      )}
    </div>
  )
}
