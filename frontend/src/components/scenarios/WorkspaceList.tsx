import { useState } from 'react'
import type { ScenarioResultDict } from '../../types/scenarios'
import { ScenarioResultView } from './ScenarioResultView'

interface WorkspaceListProps {
  scenarios: ScenarioResultDict[]
  onDelete: (name: string) => void
  onClearAll: () => void
}

export function WorkspaceList({ scenarios, onDelete, onClearAll }: WorkspaceListProps) {
  const [expandedName, setExpandedName] = useState<string | null>(null)

  function handleClearAll() {
    if (window.confirm('Clear all saved scenarios?')) onClearAll()
  }

  function handleDelete(name: string) {
    if (window.confirm(`Delete saved scenario "${name}"?`)) onDelete(name)
  }

  if (scenarios.length === 0) {
    return <p className="text-sm text-gray-500">No saved scenarios yet.</p>
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleClearAll}
        className="rounded border border-red-300 px-3 py-1.5 text-sm text-red-600"
      >
        Clear All
      </button>

      <ul className="space-y-2">
        {scenarios.map((scenario) => (
          <li key={scenario.name} className="rounded border border-gray-200 p-3 text-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-medium text-gray-900">{scenario.name}</span>{' '}
                {scenario.description && (
                  <span className="text-gray-500">{scenario.description}</span>
                )}
                {scenario.impacts.length > 0 && (
                  <p className="text-xs text-gray-500">
                    {scenario.impacts[0].metric}: {scenario.impacts[0].original_value} →{' '}
                    {scenario.impacts[0].projected_value}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() =>
                    setExpandedName(expandedName === scenario.name ? null : scenario.name)
                  }
                  className="text-blue-600 hover:underline"
                >
                  {expandedName === scenario.name ? 'Hide' : 'View'}
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(scenario.name)}
                  className="text-red-600 hover:underline"
                >
                  Delete
                </button>
              </div>
            </div>

            {expandedName === scenario.name && (
              <div className="mt-3">
                <ScenarioResultView result={scenario} />
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
