// Validated categorical palette (light mode) — see the dataviz skill's
// references/palette.md. Slot order is the CVD-safety mechanism; don't
// reorder or cycle past slot 8 without re-running the validator.
export const CHART_SERIES = {
  blue: '#2a78d6',
  orange: '#eb6834',
  aqua: '#1baf7a',
  yellow: '#eda100',
  magenta: '#e87ba4',
  green: '#008300',
  violet: '#4a3aa7',
  red: '#e34948',
} as const

export const CHART_CHROME = {
  grid: '#e1e0d9',
  axis: '#c3c2b7',
  mutedText: '#898781',
  surface: '#fcfcfb',
} as const
