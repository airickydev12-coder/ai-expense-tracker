import { useEffect, useState } from 'react'
import { getCoachingSession, listInsights } from '../api/coach'
import { CoachChat } from '../components/coach/CoachChat'
import { SeverityBadge } from '../components/coach/SeverityBadge'
import type { CoachingSessionDict, FinancialCoachInsightDict } from '../types/coach'

type InsightsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; insights: FinancialCoachInsightDict[] }

type SessionState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; session: CoachingSessionDict }

function InsightCard({ insight }: { insight: FinancialCoachInsightDict }) {
  return (
    <div className="rounded border border-gray-200 p-3 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-900">{insight.title}</span>
        <SeverityBadge value={insight.severity} />
      </div>
      <p className="mt-1 text-gray-700">{insight.message}</p>
      {insight.action && <p className="mt-1 text-xs text-gray-500">Action: {insight.action}</p>}
    </div>
  )
}

export function CoachPage() {
  const [insightsState, setInsightsState] = useState<InsightsState>({ status: 'loading' })
  const [sessionState, setSessionState] = useState<SessionState>({ status: 'loading' })
  const [expandedAdviceKey, setExpandedAdviceKey] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false

    listInsights()
      .then((insights) => {
        if (!cancelled) setInsightsState({ status: 'success', insights })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setInsightsState({ status: 'error', message })
        }
      })

    getCoachingSession()
      .then((session) => {
        if (!cancelled) setSessionState({ status: 'success', session })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setSessionState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Coach</h1>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Insights</h2>
        {insightsState.status === 'loading' && <p className="text-gray-600">Loading insights...</p>}
        {insightsState.status === 'error' && (
          <p className="text-red-600">Failed to load insights: {insightsState.message}</p>
        )}
        {insightsState.status === 'success' && (
          <div className="space-y-2">
            {insightsState.insights.length === 0 ? (
              <p className="text-sm text-gray-500">No insights available.</p>
            ) : (
              insightsState.insights.map((insight) => (
                <InsightCard key={insight.key} insight={insight} />
              ))
            )}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Full Coaching Session</h2>
        {sessionState.status === 'loading' && <p className="text-gray-600">Loading session...</p>}
        {sessionState.status === 'error' && (
          <p className="text-red-600">Failed to load coaching session: {sessionState.message}</p>
        )}
        {sessionState.status === 'success' && (
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-700">
                Health Score: <span className="font-medium">{sessionState.session.financial_health_score}</span>{' '}
                ({sessionState.session.financial_health_status})
              </p>
              <p className="mt-1 text-sm text-gray-700">{sessionState.session.summary}</p>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-900">Advice</h3>
              {sessionState.session.advice.map((advice, adviceIndex) => {
                const explanation = sessionState.session.explanations.find(
                  (e) => e.advice_key === advice.key,
                )
                const expanded = expandedAdviceKey === adviceIndex
                return (
                  <div key={adviceIndex} className="rounded border border-gray-200 p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900">{advice.title}</span>
                      <SeverityBadge value={advice.priority} />
                    </div>
                    <p className="mt-1 text-gray-700">{advice.message}</p>
                    <p className="mt-1 text-xs text-gray-500">Action: {advice.action}</p>
                    <button
                      type="button"
                      onClick={() => setExpandedAdviceKey(expanded ? null : adviceIndex)}
                      className="mt-1 text-xs text-blue-600 hover:underline"
                    >
                      {expanded ? 'Hide details' : 'Show details'}
                    </button>
                    {expanded && (
                      <div className="mt-2 space-y-1 text-xs text-gray-600">
                        <p>Reason: {advice.reason}</p>
                        <p>Expected impact: {advice.expected_impact}</p>
                        {explanation && (
                          <>
                            <p>Why it matters: {explanation.why_it_matters}</p>
                            {explanation.projected_effects.length > 0 && (
                              <ul className="list-disc pl-5">
                                {explanation.projected_effects.map((effect, idx) => (
                                  <li key={idx}>{effect}</li>
                                ))}
                              </ul>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-900">Session Insights</h3>
              {sessionState.session.insights.map((insight) => (
                <InsightCard key={insight.key} insight={insight} />
              ))}
            </div>

            {sessionState.session.next_steps.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900">Next Steps</h3>
                <ul className="list-disc pl-5 text-sm text-gray-700">
                  {sessionState.session.next_steps.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
            )}

            {sessionState.session.warnings.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900">Warnings</h3>
                <ul className="list-disc pl-5 text-sm text-red-600">
                  {sessionState.session.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      <div>
        <CoachChat />
      </div>
    </div>
  )
}
