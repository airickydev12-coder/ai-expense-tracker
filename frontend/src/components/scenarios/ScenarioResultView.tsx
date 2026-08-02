import type { ScenarioResultDict } from '../../types/scenarios'

export function BulletList({
  title,
  items,
  className,
}: {
  title: string
  items: string[]
  className: string
}) {
  if (items.length === 0) return null
  return (
    <div>
      <p className={`text-xs font-medium ${className}`}>{title}</p>
      <ul className={`list-disc pl-5 text-xs ${className}`}>
        {items.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export function ScenarioResultView({ result }: { result: ScenarioResultDict }) {
  return (
    <div className="space-y-3 rounded border border-gray-200 p-3 text-sm">
      <div>
        <h3 className="font-medium text-gray-900">{result.name}</h3>
        {result.description && <p className="text-gray-500">{result.description}</p>}
      </div>

      {result.impacts.length > 0 && (
        <table className="w-full text-left text-xs">
          <thead className="text-gray-500">
            <tr>
              <th className="pb-1">Metric</th>
              <th className="pb-1">Before</th>
              <th className="pb-1">After</th>
              <th className="pb-1">Change</th>
            </tr>
          </thead>
          <tbody>
            {result.impacts.map((impact) => (
              <tr key={impact.metric} className="border-t border-gray-100">
                <td className="py-1">{impact.metric}</td>
                <td className="py-1">{impact.original_value}</td>
                <td className="py-1">{impact.projected_value}</td>
                <td className="py-1">{impact.change}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <BulletList title="Benefits" items={result.benefits} className="text-green-700" />
      <BulletList title="Risks" items={result.risks} className="text-amber-700" />
      <BulletList title="Recommendations" items={result.recommendations} className="text-blue-700" />
    </div>
  )
}
