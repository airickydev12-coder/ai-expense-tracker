import { useState } from 'react'
import type { ScenarioRunRequest } from '../../types/scenarios'
import type { DebtResponse } from '../../types/debt'
import { ScenarioRunForm } from './ScenarioRunForm'

interface CombinedPlanBuilderProps {
  debts: DebtResponse[]
  submitting: boolean
  onSubmit: (planName: string, planDescription: string, requests: ScenarioRunRequest[]) => void
}

export function CombinedPlanBuilder({ debts, submitting, onSubmit }: CombinedPlanBuilderProps) {
  const [plan, setPlan] = useState<ScenarioRunRequest[]>([])
  const [planName, setPlanName] = useState('')
  const [planDescription, setPlanDescription] = useState('')

  function handleRemove(index: number) {
    setPlan(plan.filter((_, i) => i !== index))
  }

  function handleRunPlan() {
    onSubmit(planName.trim(), planDescription.trim(), plan)
  }

  return (
    <div className="space-y-4">
      <ScenarioRunForm
        debts={debts}
        submitLabel="Add to Plan"
        onSubmit={(request) => setPlan([...plan, request])}
      />

      <div className="space-y-2">
        <div className="flex flex-col gap-1">
          <label htmlFor="plan-name" className="text-xs text-gray-500">
            Plan Name
          </label>
          <input
            id="plan-name"
            type="text"
            value={planName}
            onChange={(e) => setPlanName(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="plan-description" className="text-xs text-gray-500">
            Plan Description (optional)
          </label>
          <input
            id="plan-description"
            type="text"
            value={planDescription}
            onChange={(e) => setPlanDescription(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>

        {plan.length === 0 ? (
          <p className="text-sm text-gray-500">No scenarios added to this plan yet.</p>
        ) : (
          <ul className="divide-y divide-gray-200 rounded border border-gray-200">
            {plan.map((request, index) => (
              <li key={index} className="flex items-center justify-between px-3 py-2 text-sm">
                <span>
                  {request.name} <span className="text-gray-500">({request.scenario_type})</span>
                </span>
                <button
                  type="button"
                  onClick={() => handleRemove(index)}
                  className="text-red-600 hover:underline"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}

        <button
          type="button"
          onClick={handleRunPlan}
          disabled={plan.length === 0 || submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          Run Combined Plan
        </button>
      </div>
    </div>
  )
}
