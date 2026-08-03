import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getTrends, listHistory, recordSnapshot } from '../api/history'
import { formatChartCurrency } from '../charts/format'
import { CHART_CHROME, CHART_SERIES } from '../charts/palette'
import type { FinancialSnapshotResponse, MetricTrend, TrendSummary } from '../types/history'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; snapshots: FinancialSnapshotResponse[]; trends: TrendSummary }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

function directionClass(direction: string): string {
  switch (direction) {
    case 'Improving':
      return 'bg-green-100 text-green-700'
    case 'Declining':
      return 'bg-red-100 text-red-700'
    case 'Stable':
      return 'bg-gray-100 text-gray-700'
    default:
      return 'bg-gray-100 text-gray-500 italic'
  }
}

function formatSnapshotDate(timestamp: string): string {
  return new Date(timestamp).toLocaleDateString()
}

function FinancialsChart({ snapshots }: { snapshots: FinancialSnapshotResponse[] }) {
  if (snapshots.length === 0) {
    return <p className="text-sm text-gray-500">No snapshots recorded yet.</p>
  }

  const data = snapshots.map((snapshot) => ({
    date: formatSnapshotDate(snapshot.timestamp),
    'Net Worth': snapshot.net_worth,
    Income: snapshot.total_income,
    Expenses: snapshot.total_expenses,
  }))

  return (
    <div className="h-64 rounded border border-gray-200 p-2" style={{ background: CHART_CHROME.surface }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CHROME.grid} vertical={false} />
          <XAxis dataKey="date" stroke={CHART_CHROME.axis} tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }} />
          <YAxis stroke={CHART_CHROME.axis} tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }} />
          <Tooltip formatter={formatChartCurrency} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line type="monotone" dataKey="Net Worth" stroke={CHART_SERIES.blue} strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="Income" stroke={CHART_SERIES.aqua} strokeWidth={2} dot={{ r: 4 }} />
          <Line type="monotone" dataKey="Expenses" stroke={CHART_SERIES.orange} strokeWidth={2} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function HealthScoreChart({ snapshots }: { snapshots: FinancialSnapshotResponse[] }) {
  if (snapshots.length === 0) {
    return <p className="text-sm text-gray-500">No snapshots recorded yet.</p>
  }

  const data = snapshots.map((snapshot) => ({
    date: formatSnapshotDate(snapshot.timestamp),
    'Health Score': snapshot.health_score,
  }))

  return (
    <div className="h-48 rounded border border-gray-200 p-2" style={{ background: CHART_CHROME.surface }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_CHROME.grid} vertical={false} />
          <XAxis dataKey="date" stroke={CHART_CHROME.axis} tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }} />
          <YAxis
            domain={[0, 100]}
            stroke={CHART_CHROME.axis}
            tick={{ fill: CHART_CHROME.mutedText, fontSize: 11 }}
          />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="Health Score"
            stroke={CHART_SERIES.blue}
            strokeWidth={2}
            dot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function TrendBadge({ label, trend }: { label: string; trend: MetricTrend }) {
  return (
    <div className="rounded border border-gray-200 p-2 text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${directionClass(trend.direction)}`}>
        {trend.direction}
      </span>
      <p className="mt-1 text-xs text-gray-600">{trend.change}</p>
    </div>
  )
}

export function HistoryPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [recording, setRecording] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    Promise.all([listHistory(), getTrends()])
      .then(([snapshots, trends]) => setState({ status: 'success', snapshots, trends }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    Promise.all([listHistory(), getTrends()])
      .then(([snapshots, trends]) => {
        if (!cancelled) setState({ status: 'success', snapshots, trends })
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
  }, [])

  function handleRecordSnapshot() {
    setRecording(true)
    setMutationError(null)
    recordSnapshot()
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to record snapshot')
      })
      .finally(() => setRecording(false))
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading history...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load history: {state.message}</p>
  }

  const { snapshots, trends } = state
  const sortedSnapshots = [...snapshots].reverse()

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">History</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <button
        type="button"
        onClick={handleRecordSnapshot}
        disabled={recording}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        Record Snapshot Now
      </button>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Trends</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <TrendBadge label="Net Worth" trend={trends.net_worth} />
          <TrendBadge label="Cash Flow" trend={trends.cash_flow} />
          <TrendBadge label="Income" trend={trends.income} />
          <TrendBadge label="Expenses" trend={trends.expenses} />
          <TrendBadge label="Health Score" trend={trends.health_score} />
          <div className="rounded border border-gray-200 p-2 text-center">
            <p className="text-xs text-gray-500">Overall Momentum</p>
            <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${directionClass(trends.overall_momentum)}`}>
              {trends.overall_momentum}
            </span>
          </div>
        </div>
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Net Worth, Income &amp; Expenses</h2>
        <FinancialsChart snapshots={snapshots} />
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Health Score</h2>
        <HealthScoreChart snapshots={snapshots} />
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Snapshots</h2>
        {sortedSnapshots.length === 0 ? (
          <p className="text-sm text-gray-500">No snapshots recorded yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="text-gray-500">
              <tr>
                <th className="pb-1">Recorded</th>
                <th className="pb-1">Net Worth</th>
                <th className="pb-1">Health</th>
              </tr>
            </thead>
            <tbody>
              {sortedSnapshots.map((snapshot) => (
                <tr key={snapshot.timestamp} className="border-t border-gray-200">
                  <td className="py-1">{new Date(snapshot.timestamp).toLocaleString()}</td>
                  <td className="py-1">{formatCurrency(snapshot.net_worth)}</td>
                  <td className="py-1">
                    {snapshot.health_score} ({snapshot.health_status})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
