import { useState } from 'react'
import type { FormEvent } from 'react'
import { SCENARIO_TYPES } from '../../types/scenarios'
import type { ScenarioRunRequest, ScenarioType } from '../../types/scenarios'
import type { DebtResponse } from '../../types/debt'
import { EMPTY_PARAMS_FORM_STATE, buildScenarioParameters } from './scenarioParams'
import { ScenarioParamsFields } from './ScenarioParamsFields'

interface ScenarioRunFormProps {
  debts: DebtResponse[]
  submitLabel: string
  onSubmit: (request: ScenarioRunRequest) => void
  secondaryLabel?: string
  onSecondarySubmit?: (request: ScenarioRunRequest) => void
  submitting?: boolean
}

export function ScenarioRunForm({
  debts,
  submitLabel,
  onSubmit,
  secondaryLabel,
  onSecondarySubmit,
  submitting,
}: ScenarioRunFormProps) {
  const [scenarioType, setScenarioType] = useState<ScenarioType>(SCENARIO_TYPES[0])
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [paramsValues, setParamsValues] = useState(EMPTY_PARAMS_FORM_STATE)
  const [formError, setFormError] = useState<string | null>(null)

  function buildRequest(): ScenarioRunRequest | null {
    if (!name.trim()) {
      setFormError('Name is required.')
      return null
    }

    const result = buildScenarioParameters(scenarioType, paramsValues)
    if ('error' in result) {
      setFormError(result.error)
      return null
    }

    setFormError(null)
    return {
      scenario_type: scenarioType,
      name: name.trim(),
      description: description.trim() || undefined,
      parameters: result.parameters,
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const request = buildRequest()
    if (request) onSubmit(request)
  }

  function handleSecondarySubmit() {
    const request = buildRequest()
    if (request && onSecondarySubmit) onSecondarySubmit(request)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="scenario-type" className="text-xs text-gray-500">
          Scenario Type
        </label>
        <select
          id="scenario-type"
          value={scenarioType}
          onChange={(e) => {
            setScenarioType(e.target.value as ScenarioType)
            setParamsValues(EMPTY_PARAMS_FORM_STATE)
          }}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {SCENARIO_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="scenario-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="scenario-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="scenario-description" className="text-xs text-gray-500">
          Description (optional)
        </label>
        <input
          id="scenario-description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <ScenarioParamsFields
        scenarioType={scenarioType}
        values={paramsValues}
        onChange={setParamsValues}
        debts={debts}
      />

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitLabel}
        </button>
        {secondaryLabel && onSecondarySubmit && (
          <button
            type="button"
            onClick={handleSecondarySubmit}
            disabled={submitting}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700 disabled:opacity-50"
          >
            {secondaryLabel}
          </button>
        )}
      </div>
    </form>
  )
}
