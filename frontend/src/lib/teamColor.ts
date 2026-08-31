/*
 * Crest colours. Clubs at this level have colours but no asset pipeline, so the
 * disc colour is derived from the club name and stays put for the life of the
 * name. Every value is dark enough for white initials (>= 6:1).
 */
const CREST_COLORS = [
  '#0B6E4F', // pitch green
  '#1F4E79', // navy
  '#7A1F2B', // claret
  '#2E5E3A', // forest
  '#4A3B8C', // violet
  '#8A4B12', // ochre
  '#175E63', // teal
  '#5C2E6E', // plum
  '#1D3557', // midnight
  '#6B2D2D', // maroon
  '#37474F', // slate
  '#0F5257', // deep teal
] as const

function hash(value: string): number {
  let result = 0
  for (let index = 0; index < value.length; index += 1) {
    result = (result * 31 + value.charCodeAt(index)) >>> 0
  }
  return result
}

export function teamColor(name: string): string {
  return CREST_COLORS[hash(name) % CREST_COLORS.length]
}

/** "Stal Łańcut" -> "SŁ", "Resovia II" -> "RI", "Karpaty" -> "KA". */
export function teamInitials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
}
