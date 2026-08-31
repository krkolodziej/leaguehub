/*
 * Crest colours. Clubs at this level have colours but no asset pipeline, so the
 * disc colour is derived from the club name and stays put for the life of the
 * name.
 *
 * The hue and darkness both come from the name; saturation is fixed, which keeps
 * every crest in the same deep, enamel-sign register whichever hue it lands on.
 * Lightness is then stepped down until white initials clear WCAG AA, because a
 * mid-lightness yellow and a mid-lightness blue are nowhere near equally bright.
 * A fixed list of twelve colours was tried first and abandoned: twelve clubs in
 * twelve slots collide constantly, and two identically coloured crests in one
 * fixture is the exact case the crest exists to prevent.
 */
const SATURATION = 0.5
// Twelve hues 30 degrees apart, three darkness tiers. A free-running hue put two
// clubs 30 degrees apart in the same green band, which reads as one colour at
// crest size; quantising guarantees any two differing crests differ visibly.
const HUE_STEPS = 12
const LIGHTNESS_TIERS = [0.24, 0.32, 0.4]
const MIN_CONTRAST = 4.5

function hash(value: string): number {
  let result = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    result ^= value.charCodeAt(index)
    result = Math.imul(result, 16777619) >>> 0
  }
  return result
}

function hslToRgb(hue: number, saturation: number, lightness: number): [number, number, number] {
  const chroma = (1 - Math.abs(2 * lightness - 1)) * saturation
  const secondary = chroma * (1 - Math.abs(((hue / 60) % 2) - 1))
  const offset = lightness - chroma / 2
  const [red, green, blue] =
    hue < 60 ? [chroma, secondary, 0]
    : hue < 120 ? [secondary, chroma, 0]
    : hue < 180 ? [0, chroma, secondary]
    : hue < 240 ? [0, secondary, chroma]
    : hue < 300 ? [secondary, 0, chroma]
    : [chroma, 0, secondary]
  return [
    Math.round((red + offset) * 255),
    Math.round((green + offset) * 255),
    Math.round((blue + offset) * 255),
  ]
}

function relativeLuminance([red, green, blue]: [number, number, number]): number {
  const channel = (value: number) => {
    const ratio = value / 255
    return ratio <= 0.03928 ? ratio / 12.92 : ((ratio + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * channel(red) + 0.7152 * channel(green) + 0.0722 * channel(blue)
}

function toHex([red, green, blue]: [number, number, number]): string {
  return `#${[red, green, blue].map((value) => value.toString(16).padStart(2, '0')).join('')}`
}

export function teamColor(name: string): string {
  const fingerprint = hash(name)
  const hue = (fingerprint % HUE_STEPS) * (360 / HUE_STEPS)
  let lightness = LIGHTNESS_TIERS[Math.floor(fingerprint / HUE_STEPS) % LIGHTNESS_TIERS.length]
  let rgb = hslToRgb(hue, SATURATION, lightness)
  // 1.05 is white's luminance plus the 0.05 offset in the WCAG contrast formula.
  while (1.05 / (relativeLuminance(rgb) + 0.05) < MIN_CONTRAST && lightness > 0.12) {
    lightness -= 0.02
    rgb = hslToRgb(hue, SATURATION, lightness)
  }
  return toHex(rgb)
}

/** "Stal Łańcut" -> "SŁ", "Resovia II" -> "RI", "Karpaty" -> "KA". */
export function teamInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}
