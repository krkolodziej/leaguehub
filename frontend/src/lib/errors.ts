import { ApiError } from './api'

// The API reports a bad sign-in as a code rather than a field error, so the
// wording lives here instead of leaking a generic validation message.
const MESSAGE_BY_CODE: Record<string, string> = {
  invalid_credentials: 'Email or password is incorrect.',
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return (error.code && MESSAGE_BY_CODE[error.code]) ?? error.message
  }
  if (error instanceof Error) return error.message
  return 'Something went wrong. Please try again.'
}

/** Flatten the API `fields` payload into one message per field. */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.fields) return {}
  const messages: Record<string, string> = {}
  for (const [field, value] of Object.entries(error.fields)) {
    const message = Array.isArray(value) ? value.join(' ') : value
    if (typeof message === 'string' && message) messages[field] = message
  }
  return messages
}
