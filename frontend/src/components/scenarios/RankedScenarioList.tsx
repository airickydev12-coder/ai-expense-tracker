import { useState } from 'react'
import type { RankedScenario } from '../../types/scenarios'
import { ScenarioResultView } from './ScenarioResultView'

export function RankedScenarioList({ scenarios }: { scenarios: RankedScenario[] }) {
  const [expandedRank, setExpandedRank] = useState<number | null>(null)

  if (scenarios.length === 0) {
    return <p className="text-sm text-gray-500">No ranked scenarios.</p>
  }

  return (
    <ul className="space-y-2">
      {scenarios.map((scenario) => (
        <li key={scenario.rank} className="rounded border border-gray-200 p-3 text-sm">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium text-gray-900">
                #{scenario.rank} {scenario.scenario_name}
              </span>{' '}
              <span className="text-gray-500">
                (score {scenario.score.toFixed(2)}, {scenario.scenario_score.rating})
              </span>
              <p className="text-xs text-gray-500">{scenario.scenario_score.recommendation}</p>
            </div>
            <button
              type="button"
              onClick={() => setExpandedRank(expandedRank === scenario.rank ? null : scenario.rank)}
              className="text-blue-600 hover:underline"
            >
              {expandedRank === scenario.rank ? 'Collapse' : 'Expand'}
            </button>
          </div>

          {expandedRank === scenario.rank && (
            <div className="mt-3 space-y-3">
              {scenario.scenario_score.components.length > 0 && (
                <table className="w-full text-left text-xs">
                  <thead className="text-gray-500">
                    <tr>
                      <th className="pb-1">Component</th>
                      <th className="pb-1">Score</th>
                      <th className="pb-1">Weight</th>
                      <th className="pb-1">Weighted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scenario.scenario_score.components.map((component) => (
                      <tr key={component.name} className="border-t border-gray-100">
                        <td className="py-1">{component.name}</td>
                        <td className="py-1">{component.score.toFixed(2)}</td>
                        <td className="py-1">{component.weight.toFixed(2)}</td>
                        <td className="py-1">{component.weighted_score.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
              <ScenarioResultView result={scenario.result} />
            </div>
          )}
        </li>
      ))}
    </ul>
  )
}
