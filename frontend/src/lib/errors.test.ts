import { describe, expect, it } from 'vitest'

import { ApiError } from './api'
import { errorMessage } from './errors'

describe('errorMessage', () => {
  it('uses API error details when available', () => {
    expect(errorMessage(new ApiError(409, { detail: 'Already exists.' }))).toBe('Already exists.')
  })

  it('falls back for unknown values', () => {
    expect(errorMessage({ reason: 'unknown' })).toBe('Something went wrong. Please try again.')
  })
})
