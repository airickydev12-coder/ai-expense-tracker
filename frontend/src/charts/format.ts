export function formatChartNumber(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(2) : String(value)
}

export function formatChartCurrency(value: unknown): string {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : String(value)
}
