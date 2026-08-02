const SEVERITY_CLASSES: Record<string, string> = {
  Positive: 'bg-green-100 text-green-700',
  Informational: 'bg-blue-100 text-blue-700',
  Warning: 'bg-amber-100 text-amber-700',
  Critical: 'bg-red-100 text-red-700',
}

export function SeverityBadge({ value }: { value: string }) {
  const cls = SEVERITY_CLASSES[value] ?? 'bg-gray-100 text-gray-700'
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{value}</span>
}
