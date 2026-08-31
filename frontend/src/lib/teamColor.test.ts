import { describe, expect, it } from 'vitest'

import { teamColor, teamInitials } from './teamColor'

const CLUBS = [
  'Stal Łańcut',
  'Karpaty Krosno',
  'Resovia II',
  'Polonia Przemyśl',
  'Sokół Sieniawa',
  'Czarni Jasło',
  'Wisłoka Dębica',
  'Orzeł Przeworsk',
  'Izolator Boguchwała',
  'Błękitni Ropczyce',
  'Piast Tuczempy',
  'Sanovia Lesko',
]

function luminance(hex: string) {
  const channel = (offset: number) => {
    const ratio = parseInt(hex.slice(offset, offset + 2), 16) / 255
    return ratio <= 0.03928 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * channel(1) + 0.7152 * channel(3) + 0.0722 * channel(5)
}

describe('teamColor', () => {
  it('is deterministic for a given club name', () => {
    expect(teamColor('Stal Łańcut')).toBe(teamColor('Stal Łańcut'))
    expect(teamColor('Stal Łańcut')).not.toBe(teamColor('Karpaty Krosno'))
  })

  it('gives every club in the division a visibly separate colour', () => {
    expect(new Set(CLUBS.map(teamColor)).size).toBe(CLUBS.length)
  })

  it('separates the two sides of a fixture rather than shading them alike', () => {
    // These two collided under the previous free-running hue.
    expect(teamColor('Resovia II')).not.toBe(teamColor('Błękitni Ropczyce'))
    const channels = (hex: string) => [1, 3, 5].map((offset) => parseInt(hex.slice(offset, offset + 2), 16))
    const [a, b] = [teamColor('Resovia II'), teamColor('Błękitni Ropczyce')].map(channels)
    const distance = Math.max(...a.map((value, index) => Math.abs(value - b[index])))
    expect(distance).toBeGreaterThan(40)
  })

  it('stays dark enough for white initials to pass WCAG AA', () => {
    for (const club of CLUBS) {
      const contrast = 1.05 / (luminance(teamColor(club)) + 0.05)
      expect(contrast, `${club} -> ${teamColor(club)}`).toBeGreaterThanOrEqual(4.5)
    }
  })
})

describe('teamInitials', () => {
  it('takes the first letter of the first two words', () => {
    expect(teamInitials('Stal Łańcut')).toBe('SŁ')
    expect(teamInitials('Resovia II')).toBe('RI')
  })

  it('falls back to the first two letters of a single word', () => {
    expect(teamInitials('Karpaty')).toBe('KA')
  })
})
