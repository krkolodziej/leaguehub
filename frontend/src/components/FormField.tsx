import type { InputHTMLAttributes } from 'react'

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
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={description}
        {...inputProps}
      />
      {error && <span className="field-error" id={`${id}-error`}>{error}</span>}
      {!error && hint && <span className="field-hint" id={`${id}-hint`}>{hint}</span>}
    </div>
  )
}
