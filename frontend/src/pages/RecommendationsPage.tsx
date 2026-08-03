import { useEffect, useState } from 'react'
import {
  completeRecommendation,
  dismissRecommendation,
  getFilteredRecommendations,
  getRecommendationCategories,
  getRecommendationPriorities,
  suppressRecommendation,
} from '../api/recommendations'
import type {
  RecommendationCategoryResponse,
  RecommendationPriorityResponse,
  RecommendationResponse,
} from '../types/recommendations'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; recommendations: RecommendationResponse[] }

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-800',
  HIGH: 'bg-orange-100 text-orange-800',
  MEDIUM: 'bg-amber-100 text-amber-800',
  LOW: 'bg-gray-100 text-gray-700',
}

function PriorityBadge({ priority }: { priority: string }) {
  const className = PRIORITY_STYLES[priority] ?? 'bg-gray-100 text-gray-700'
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${className}`}>{priority}</span>
}

export function RecommendationsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [categories, setCategories] = useState<RecommendationCategoryResponse[]>([])
  const [priorities, setPriorities] = useState<RecommendationPriorityResponse[]>([])
  const [categoryFilter, setCategoryFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actioningKey, setActioningKey] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    getFilteredRecommendations({ category: categoryFilter, priority: priorityFilter })
      .then((recommendations) => setState({ status: 'success', recommendations }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    Promise.all([getRecommendationCategories(), getRecommendationPriorities()])
      .then(([categoryList, priorityList]) => {
        if (!cancelled) {
          setCategories(categoryList)
          setPriorities(priorityList)
        }
      })
      .catch(() => {
        // Filter dropdowns are a non-critical enhancement — leave them empty on failure.
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    setState({ status: 'loading' })
    getFilteredRecommendations({ category: categoryFilter, priority: priorityFilter })
      .then((recommendations) => {
        if (!cancelled) setState({ status: 'success', recommendations })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [categoryFilter, priorityFilter])

  function handleAction(
    action: (key: string) => Promise<unknown>,
    recommendation: RecommendationResponse,
  ) {
    setActionError(null)
    setActioningKey(recommendation.key)
    action(recommendation.key)
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to update recommendation')
      })
      .finally(() => setActioningKey(null))
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Recommendations</h1>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      <div className="flex flex-wrap gap-4">
        <label className="flex flex-col gap-1 text-xs text-gray-500">
          Category
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm text-gray-900"
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.name} value={category.value}>
                {category.value}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-gray-500">
          Priority
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm text-gray-900"
          >
            <option value="">All priorities</option>
            {priorities.map((priority) => (
              <option key={priority.name} value={priority.name}>
                {priority.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {state.status === 'loading' && <p className="text-sm text-gray-600">Loading recommendations...</p>}

      {state.status === 'error' && (
        <p className="text-sm text-red-600">Failed to load recommendations: {state.message}</p>
      )}

      {state.status === 'success' && (
        <>
          {state.recommendations.length === 0 ? (
            <p className="text-sm text-gray-500">No recommendations right now.</p>
          ) : (
            <ul className="divide-y divide-gray-200 rounded border border-gray-200">
              {state.recommendations.map((recommendation) => (
                <li key={recommendation.key} className="space-y-2 px-3 py-3 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <PriorityBadge priority={recommendation.priority} />
                    <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                      {recommendation.category}
                    </span>
                    <span className="font-medium text-gray-900">{recommendation.title}</span>
                  </div>
                  <p className="text-gray-700">{recommendation.message}</p>
                  {recommendation.is_actionable && (
                    <p className="text-gray-600">
                      <span className="font-medium">Suggested action:</span> {recommendation.action}
                    </p>
                  )}
                  <div className="flex items-center gap-3 pt-1">
                    <button
                      type="button"
                      disabled={actioningKey === recommendation.key}
                      onClick={() => handleAction(completeRecommendation, recommendation)}
                      className="text-green-600 hover:underline disabled:opacity-50"
                    >
                      Complete
                    </button>
                    <button
                      type="button"
                      disabled={actioningKey === recommendation.key}
                      onClick={() => handleAction(dismissRecommendation, recommendation)}
                      className="text-blue-600 hover:underline disabled:opacity-50"
                    >
                      Dismiss
                    </button>
                    <button
                      type="button"
                      disabled={actioningKey === recommendation.key}
                      onClick={() => handleAction(suppressRecommendation, recommendation)}
                      className="text-red-600 hover:underline disabled:opacity-50"
                    >
                      Suppress
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
