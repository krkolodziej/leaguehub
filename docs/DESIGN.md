# LeagueHub design plan

The subject is Polish amateur football administration. The reference material is the
printed world that surrounds it: regional newspaper sports pages, matchday programmes
run off on two-colour presses, the ruled league tables pinned up in a clubhouse, and
enamel club signage. Not application dashboards.

## Palette

Six values. Everything else is a tint of these.

| Token | Hex | Role |
| --- | --- | --- |
| `paper` | `#ECEEE9` | Page ground. A cool grey-green newsprint, not a warm cream. |
| `ink` | `#14171A` | Body text, headings, table rules. Never a page background. |
| `pitch` | `#0B6E4F` | Structure and action: table headers, links, primary buttons, the promotion rule. |
| `chalk` | `#CBD1C9` | Hairlines, column dividers, input borders. |
| `booking` | `#E8B411` | **Yellow card only.** |
| `sending-off` | `#B3261E` | **Red card only.** |

`ink` at 70% gives the secondary text tone (`#4F565C` against paper) used for meta
lines. The ground sits a clear step below the white panel surface on purpose: an
earlier pass put near-white panels on a near-white ground, and the separation was
so slight that the page read as unstyled rather than as calm.

The two signal colours are spent entirely on their sport meaning. A yellow chip in this
interface is a caution and nothing else; a red chip is a dismissal and nothing else. This
has consequences the rest of the UI has to absorb:

- **Errors and destructive actions do not use red.** They are set in `ink` with a 3px
  `ink` rule down the left edge. Weight and position carry the alarm, not hue.
- **`LIVE` is not red either.** It is the only element in the product allowed to move: a
  small pulsing disc. Motion is the signal, so the treatment survives both colour
  blindness and `prefers-reduced-motion` (where it falls back to a filled ring).

Contrast, measured in the running app against `paper`: headings 15.4:1, secondary
ink 6.4:1 (7.5:1 on a white panel), `pitch` 5.4:1. White on `pitch` is 6.3:1. All
pass AA for body text.

No dark mode.

## Type

Two families, both with true tabular lining figures — mandatory, because half this
product is numeric columns that must align.

Both are **self-hosted** through `@fontsource`, restricted to the `latin` and
`latin-ext` subsets. A font CDN was used first, but the entire typographic case
collapses to a system fallback the moment that request is slow or blocked, and
`latin-ext` is not optional when half the club names carry Polish diacritics.

- **IBM Plex Sans** — interface text, forms, prose. A slightly bureaucratic grotesque
  that suits league administration.
- **IBM Plex Sans Condensed** — page titles, team names inside tables, all numerals,
  scores. Condensed buys horizontal room in a fourteen-column table and reads as
  scoreboard/programme lettering rather than as a web app.

`font-variant-numeric: tabular-nums lining-nums` is set on every table, score and stat.

| Step | Size | Role |
| --- | --- | --- |
| `2xs` | 12px | Table column heads, form-guide marks |
| `xs` | 13px | Meta lines, captions |
| `sm` | 14px | Dense table cells, secondary UI |
| `base` | 16px | Body |
| `lg` | 20px | Section titles |
| `xl` | 30px | Page titles |
| `2xl` | 36px | Match card scores |
| `score` | 64px | Match detail scoreline |

The first pass set every step two sizes smaller and headings at 600. On a real
screen that read as timid rather than as dense, so the whole scale moved up and
headings went to 700.

Headings are set in condensed at 700, tight (`-0.015em`), and are **not** all-caps with letter
spacing. Column heads in tables are the one place small caps appear, because printed
tables actually do that.

## Layout

The page is a single column on a `paper` ground with a maximum measure of 1120px. There
is no sidebar. Sections are separated by rules and whitespace rather than by boxing
everything — the standings table in particular is typeset directly onto the page, full
bleed to its container, the way a newspaper sets one. Boxed surfaces are reserved for
things that genuinely are discrete objects: a match card, a crest, a form panel. On
narrow screens the table keeps position, crest, team and points, and scrolls the middle
columns horizontally inside its own container.

### League dashboard

```
+--------------------------------------------------------------+
| LeagueHub    Dashboard                  [bell] 3   Marek  [>] |
+==============================================================+
|  < Podkarpacka Liga Amatorska                                 |
|                                                               |
|  LIGA OKREGOWA                             Season [2026/27 v] |
|  ------------------------------------------------------------ |
|  Overview | Fixtures | Table | Teams | Statistics              |
|  =========                                                     |
|                                                                |
|  NEXT MATCHES                    TABLE                         |
|  --------------------------      ---------------------------- |
|  R14   (o) LIVE  63'              1  (S) Stal Lancut   13  28  |
|  Blekitni   1 : 1   Stal          2  (R) Resovia II    13  24  |
|  ..........................       3  (S) Sokol Sien.   13  22  |
|  R14   Sat 4 Sep  11:00           ---------------------------- |
|  Czarni     -  :  -   Karpaty    11  (I) Izolator      12   8  |
|                                  12  (P) Piast Tucz.   12   7  |
|                                                                |
|  RECENT RESULTS                  TOP SCORERS                   |
|  --------------------------      ---------------------------- |
|  FT    Stal   3 : 1   Piast       1  Szymon Stepien        12  |
|  FT    Sokol  0 : 0   Czarni      2  Sebastian Dudek       11  |
+----------------------------------------------------------------+
```

### Standings table

```
  POS  TEAM                   MP   W   D   L   GF   GA    GD  PTS  FORM
 ======================================================================
| 1   (S) Stal Lancut         13   9   1   3   23   11   +12   28  W W L W W
| 2   (R) Resovia II          13   7   3   3   27   11   +16   24  D W W D W
| 3   (S) Sokol Sieniawa      13   7   1   5   15   13    +2   22  W L W W L
+---------------------------------------------------------------------- promotion
  4   (C) Czarni Jaslo        13   6   3   4   16   16     0   21  L D W D W
  ...
  10  (P) Polonia Przemysl    12   4   3   5   15   18    -3   15  L L D W L
+---------------------------------------------------------------------- relegation
: 11  (I) Izolator Boguchwala 12   2   2   8   13   26   -13    8  L L W L L
: 12  (P) Piast Tuczempy      12   1   4   7   11   21   -10    7  D L L D L

  |  = 3px pitch marginal band     : = 3px ink marginal band
  (S) = crest disc, colour derived from the team name
```

The zones are marked in the **margin**, not by tinting whole rows. A newspaper prints a
rule and a marginal bar; tinted row backgrounds are a spreadsheet idiom and they fight
the form-guide colours sitting in the same row.

## Principles

Football hands this interface two things that no project tracker has, and both are load
bearing. Yellow and red already carry fixed, universally understood meanings, so they are
treated as reserved vocabulary rather than as a decorative accent pair — which in turn
forces every other status to be expressed through structure, weight, or motion. The
standings table is not one view among several but the artefact the whole competition
exists to produce, so it gets the typographic care of printed matter: tabular figures,
hairline column rules, a position gutter, and marginal zone bars. Scores are set at
scoreboard scale because a result is the single fact a reader came for, and everything
around a score is caption to it. The form guide, the crest disc and the round marker are
included because a reader of league tables expects them, and their absence reads as an
incomplete table.

## Critique of the first draft

Before building I checked the plan against the question: would I have produced this for a
CRM or a project tracker? Parts of it, yes. Those parts were wrong and were changed.

1. **Everything was in a rounded card with a soft shadow.** That is the default
   component-library reflex and it is what a project tracker looks like. Changed: the
   standings table is typeset onto the page with rules and no wrapper; boxes are reserved
   for match cards, crests and form panels. Rules and space do the separating.
2. **Red was doing double duty** as the error/destructive colour *and* the red-card
   colour. That wastes the one piece of colour vocabulary the domain gives away free, and
   it makes a failed form look like a sending-off. Changed: red and yellow are reserved
   for cards; errors use ink plus a heavy left rule.
3. **`LIVE` was a red badge** — the broadcast cliché, and it collided with (2). Changed:
   `LIVE` is the only moving element in the product, which makes motion the signal and
   frees the colour.
4. **The type plan was one neutral UI sans throughout.** That ignores the actual
   typographic problem, which is a dense numeric grid and a very large score. Changed: a
   condensed cut carries tables, numerals and scores; the plain cut carries prose.
5. **Zone marking was a tinted row background.** Spreadsheet idiom, and it clashes with
   the form-guide marks in the same row. Changed to marginal bars.

What survived the critique unchanged is the part that came from the subject rather than
from habit: the reserved card colours, the printed-table treatment, scoreboard numerals,
the form guide, and the crest disc.
