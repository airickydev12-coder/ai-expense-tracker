import { useEffect, useState } from 'react'
import {
  deleteNote,
  explainRecommendation,
  getCoachingSession,
  getFinancialNarrative,
  getMonthlyReview,
  listInsights,
  listNotes,
  saveMonthlyReview,
  saveNote,
} from '../api/coach'
import { listRecommendations } from '../api/recommendations'
import { CoachChat } from '../components/coach/CoachChat'
import { SeverityBadge } from '../components/coach/SeverityBadge'
import type {
  CoachingSessionDict,
  FinancialCoachInsightDict,
  MonthlyReviewDict,
  RecommendationExplanationDict,
  SavedNoteDict,
} from '../types/coach'
import type { RecommendationResponse } from '../types/recommendations'

type InsightsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; insights: FinancialCoachInsightDict[] }

type SessionState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; session: CoachingSessionDict }

type NarrativeState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; narrative: string }

type RecommendationsState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; recommendations: RecommendationResponse[] }

type ExplanationState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; explanation: RecommendationExplanationDict }

type MonthlyReviewState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; review: MonthlyReviewDict }

type NotesState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; notes: SavedNoteDict[] }

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

function RecommendationCard({
  recommendation,
  explanationState,
  onExplain,
}: {
  recommendation: RecommendationResponse
  explanationState: ExplanationState | undefined
  onExplain: () => void
}) {
  return (
    <div className="rounded border border-gray-200 p-3 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-900">
          {recommendation.title} <span className="text-xs text-gray-500">({recommendation.category})</span>
        </span>
        <SeverityBadge value={recommendation.priority} />
      </div>
      <p className="mt-1 text-gray-700">{recommendation.message}</p>
      <p className="mt-1 text-xs text-gray-500">Action: {recommendation.action}</p>

      {!explanationState && (
        <button
          type="button"
          onClick={onExplain}
          className="mt-2 text-xs text-blue-600 hover:underline"
        >
          Explain
        </button>
      )}

      {explanationState?.status === 'loading' && (
        <p className="mt-2 text-xs text-gray-500">Loading explanation...</p>
      )}
      {explanationState?.status === 'error' && (
        <p className="mt-2 text-xs text-red-600">Failed to load explanation: {explanationState.message}</p>
      )}
      {explanationState?.status === 'success' && (
        <div className="mt-2 space-y-1 rounded bg-gray-50 p-2 text-xs text-gray-700">
          <p>Reason: {explanationState.explanation.reason}</p>
          <p>Expected impact: {explanationState.explanation.expected_impact}</p>
          <p>Confidence: {explanationState.explanation.confidence}</p>
          {explanationState.explanation.assumptions.length > 0 && (
            <div>
              <span>Assumptions:</span>
              <ul className="list-disc pl-5">
                {explanationState.explanation.assumptions.map((assumption, idx) => (
                  <li key={idx}>{assumption}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function CoachPage() {
  const [narrativeState, setNarrativeState] = useState<NarrativeState>({ status: 'loading' })
  const [insightsState, setInsightsState] = useState<InsightsState>({ status: 'loading' })
  const [sessionState, setSessionState] = useState<SessionState>({ status: 'loading' })
  const [recommendationsState, setRecommendationsState] = useState<RecommendationsState>({
    status: 'loading',
  })
  const [explanations, setExplanations] = useState<Record<string, ExplanationState>>({})
  const [monthlyReviewState, setMonthlyReviewState] = useState<MonthlyReviewState>({ status: 'loading' })
  const [savingReview, setSavingReview] = useState(false)
  const [saveReviewError, setSaveReviewError] = useState<string | null>(null)
  const [expandedAdviceKey, setExpandedAdviceKey] = useState<number | null>(null)
  const [notesState, setNotesState] = useState<NotesState>({ status: 'loading' })
  const [noteTitle, setNoteTitle] = useState('')
  const [noteContent, setNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [saveNoteError, setSaveNoteError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    getFinancialNarrative()
      .then((result) => {
        if (!cancelled) setNarrativeState({ status: 'success', narrative: result.narrative })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setNarrativeState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

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

  useEffect(() => {
    let cancelled = false

    listRecommendations()
      .then((recommendations) => {
        if (!cancelled) setRecommendationsState({ status: 'success', recommendations })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setRecommendationsState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    getMonthlyReview()
      .then((review) => {
        if (!cancelled) setMonthlyReviewState({ status: 'success', review })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setMonthlyReviewState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    listNotes()
      .then((notes) => {
        if (!cancelled) setNotesState({ status: 'success', notes })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Unknown error'
          setNotesState({ status: 'error', message })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  function handleExplain(recommendationKey: string) {
    setExplanations((prev) => ({ ...prev, [recommendationKey]: { status: 'loading' } }))

    explainRecommendation(recommendationKey)
      .then((explanation) => {
        setExplanations((prev) => ({
          ...prev,
          [recommendationKey]: { status: 'success', explanation },
        }))
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setExplanations((prev) => ({
          ...prev,
          [recommendationKey]: { status: 'error', message },
        }))
      })
  }

  function handleSaveReview() {
    setSavingReview(true)
    setSaveReviewError(null)
    saveMonthlyReview()
      .then((review) => setMonthlyReviewState({ status: 'success', review }))
      .catch((err: unknown) => {
        setSaveReviewError(err instanceof Error ? err.message : 'Failed to save review')
      })
      .finally(() => setSavingReview(false))
  }

  function handleSaveNote() {
    setSavingNote(true)
    setSaveNoteError(null)
    saveNote(noteTitle, noteContent)
      .then((note) => {
        setNotesState((prev) => ({
          status: 'success',
          notes: [note, ...(prev.status === 'success' ? prev.notes : [])],
        }))
        setNoteTitle('')
        setNoteContent('')
      })
      .catch((err: unknown) => {
        setSaveNoteError(err instanceof Error ? err.message : 'Failed to save note')
      })
      .finally(() => setSavingNote(false))
  }

  function handleDeleteNote(noteId: number) {
    deleteNote(noteId)
      .then(() => {
        setNotesState((prev) => ({
          status: 'success',
          notes: prev.status === 'success' ? prev.notes.filter((note) => note.id !== noteId) : [],
        }))
      })
      .catch(() => {
        // Deletion failures are non-critical; the note simply stays in the list.
      })
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Coach</h1>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Financial Narrative</h2>
        {narrativeState.status === 'loading' && <p className="text-gray-600">Loading narrative...</p>}
        {narrativeState.status === 'error' && (
          <p className="text-red-600">Failed to load narrative: {narrativeState.message}</p>
        )}
        {narrativeState.status === 'success' && (
          <p className="text-sm text-gray-700">{narrativeState.narrative}</p>
        )}
      </div>

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
        <h2 className="mb-2 text-lg font-medium text-gray-900">Recommendations</h2>
        {recommendationsState.status === 'loading' && (
          <p className="text-gray-600">Loading recommendations...</p>
        )}
        {recommendationsState.status === 'error' && (
          <p className="text-red-600">
            Failed to load recommendations: {recommendationsState.message}
          </p>
        )}
        {recommendationsState.status === 'success' && (
          <div className="space-y-2">
            {recommendationsState.recommendations.length === 0 ? (
              <p className="text-sm text-gray-500">No recommendations right now.</p>
            ) : (
              recommendationsState.recommendations.map((recommendation) => (
                <RecommendationCard
                  key={recommendation.key}
                  recommendation={recommendation}
                  explanationState={explanations[recommendation.key]}
                  onExplain={() => handleExplain(recommendation.key)}
                />
              ))
            )}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Monthly Review</h2>
        {monthlyReviewState.status === 'loading' && <p className="text-gray-600">Loading monthly review...</p>}
        {monthlyReviewState.status === 'error' && (
          <p className="text-red-600">Failed to load monthly review: {monthlyReviewState.message}</p>
        )}
        {monthlyReviewState.status === 'success' && (
          <div className="space-y-3 text-sm">
            {monthlyReviewState.review.status !== 'ok' ? (
              <p className="text-gray-600">{monthlyReviewState.review.message}</p>
            ) : (
              <>
                {saveReviewError && <p className="text-red-600">{saveReviewError}</p>}
                {monthlyReviewState.review.generated_at ? (
                  <p className="text-xs text-gray-500">
                    Saved {new Date(monthlyReviewState.review.generated_at).toLocaleString()}
                  </p>
                ) : (
                  <button
                    type="button"
                    onClick={handleSaveReview}
                    disabled={savingReview}
                    className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
                  >
                    {savingReview ? 'Saving...' : 'Save This Review'}
                  </button>
                )}
                <p className="text-gray-700">{monthlyReviewState.review.overall_summary}</p>
                {monthlyReviewState.review.income_vs_expenses && (
                  <p className="text-gray-700">{monthlyReviewState.review.income_vs_expenses.narrative}</p>
                )}
                {monthlyReviewState.review.cash_flow && (
                  <p className="text-gray-700">{monthlyReviewState.review.cash_flow.narrative}</p>
                )}
                {monthlyReviewState.review.debt_progress && (
                  <p className="text-gray-700">{monthlyReviewState.review.debt_progress.narrative}</p>
                )}
                {monthlyReviewState.review.savings_progress && (
                  <p className="text-gray-700">{monthlyReviewState.review.savings_progress.narrative}</p>
                )}
                {monthlyReviewState.review.goal_status && (
                  <p className="text-gray-700">{monthlyReviewState.review.goal_status.narrative}</p>
                )}
                {monthlyReviewState.review.health_score && (
                  <p className="text-gray-700">{monthlyReviewState.review.health_score.narrative}</p>
                )}
                {monthlyReviewState.review.top_actions && monthlyReviewState.review.top_actions.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Top Actions</h3>
                    <ul className="list-disc pl-5 text-gray-700">
                      {monthlyReviewState.review.top_actions.map((action) => (
                        <li key={action.key}>{action.title}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {monthlyReviewState.review.category_trends && monthlyReviewState.review.category_trends.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Category Spending Shifts</h3>
                    <ul className="list-disc pl-5 text-gray-700">
                      {monthlyReviewState.review.category_trends.map((trend) => (
                        <li key={trend.category}>
                          {`${trend.category}: ${trend.direction === 'Increasing' ? '+' : '-'}$${Math.abs(trend.change).toFixed(2)}`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {monthlyReviewState.review.known_gaps && monthlyReviewState.review.known_gaps.length > 0 && (
                  <ul className="list-disc pl-5 text-xs text-gray-500">
                    {monthlyReviewState.review.known_gaps.map((gap, idx) => (
                      <li key={idx}>{gap}</li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>
        )}
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Notes</h2>
        <div className="mb-3 space-y-2">
          {saveNoteError && <p className="text-red-600">{saveNoteError}</p>}
          <input
            type="text"
            placeholder="Title"
            value={noteTitle}
            onChange={(e) => setNoteTitle(e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
          />
          <textarea
            placeholder="Note content"
            value={noteContent}
            onChange={(e) => setNoteContent(e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
          />
          <button
            type="button"
            onClick={handleSaveNote}
            disabled={savingNote || !noteTitle.trim() || !noteContent.trim()}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          >
            {savingNote ? 'Saving...' : 'Save Note'}
          </button>
        </div>
        {notesState.status === 'loading' && <p className="text-gray-600">Loading notes...</p>}
        {notesState.status === 'error' && (
          <p className="text-red-600">Failed to load notes: {notesState.message}</p>
        )}
        {notesState.status === 'success' && (
          <div className="space-y-2">
            {notesState.notes.length === 0 ? (
              <p className="text-sm text-gray-500">No notes saved yet.</p>
            ) : (
              notesState.notes.map((note) => (
                <div key={note.id} className="rounded border border-gray-200 p-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{note.title}</span>
                    <button
                      type="button"
                      onClick={() => handleDeleteNote(note.id)}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                  <p className="mt-1 text-gray-700">{note.content}</p>
                </div>
              ))
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
