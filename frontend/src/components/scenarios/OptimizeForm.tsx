import { useState } from 'react'
import type { FormEvent } from 'react'
import { RANKING_METRICS } from '../../types/scenarios'
import type { RankingMetric, ScenarioOptimizeRequest } from '../../types/scenarios'

interface OptimizeFormProps {
  submitting: boolean
  onSubmit: (request: ScenarioOptimizeRequest) => void
}

export function OptimizeForm({ submitting, onSubmit }: OptimizeFormProps) {
  const [limit, setLimit] = useState('')
  const [rankingMetric, setRankingMetric] = useState<RankingMetric>('Overall')
  const [horizonMonths, setHorizonMonths] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    const request: ScenarioOptimizeRequest = {}
    if (rankingMetric !== 'Overall') {
      request.ranking_metric = rankingMetric
    }

    if (limit.trim() !== '') {
      const parsedLimit = Number(limit)
      if (!Number.isInteger(parsedLimit) || parsedLimit <= 0) {
        setFormError('Limit must be a positive whole number.')
        return
      }
      request.limit = parsedLimit
    }

    if (horizonMonths.trim() !== '') {
      const parsedHorizon = Number(horizonMonths)
      if (!Number.isFinite(parsedHorizon) || parsedHorizon <= 0) {
        setFormError('Horizon must be a positive number.')
        return
      }
      request.horizon_months = parsedHorizon
    }

    setFormError(null)
    onSubmit(request)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="optimize-limit" className="text-xs text-gray-500">
          Limit (optional)
        </label>
        <input
          id="optimize-limit"
          type="number"
          min="1"
          step="1"
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="optimize-ranking-metric" className="text-xs text-gray-500">
          Ranking Metric
        </label>
        <select
          id="optimize-ranking-metric"
          value={rankingMetric}
          onChange={(e) => setRankingMetric(e.target.value as RankingMetric)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {RANKING_METRICS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="optimize-horizon-months" className="text-xs text-gray-500">
          Horizon Months (optional, defaults to 12)
        </label>
        <input
          id="optimize-horizon-months"
          type="number"
          min="1"
          step="1"
          value={horizonMonths}
          onChange={(e) => setHorizonMonths(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        Run Optimizer
      </button>
    </form>
  )
}
