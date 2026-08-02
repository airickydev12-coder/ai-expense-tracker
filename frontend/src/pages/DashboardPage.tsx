import { useEffect, useState } from 'react'
import { getDashboard } from '../api/dashboard'
import { getHealth } from '../api/health'
import type { DashboardResponse } from '../types/dashboard'
import type { HealthResponse } from '../types/health'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; dashboard: DashboardResponse; health: HealthResponse }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    Promise.all([getDashboard(), getHealth()])
      .then(([dashboard, health]) => {
        if (!cancelled) setState({ status: 'success', dashboard, health })
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

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading dashboard...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load dashboard: {state.message}</p>
  }

  const { dashboard, health } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Financial Dashboard</h1>

      <p className="text-sm text-gray-500">
        API status: <span className="font-medium text-green-600">{health.status}</span> (
        {health.service} v{health.version})
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Total Expenses" value={formatCurrency(dashboard.total_expenses)} />
        <Stat label="Average Expense" value={formatCurrency(dashboard.average_expense)} />
        <Stat label="Monthly Budget" value={formatCurrency(dashboard.monthly_budget)} />
        <Stat label="Remaining Budget" value={formatCurrency(dashboard.remaining_budget)} />
        <Stat label="Budget Used" value={`${dashboard.budget_used_percent.toFixed(1)}%`} />
        <Stat label="Budget Count" value={String(dashboard.budget_count)} />
        <Stat label="Recommendations" value={String(dashboard.recommendation_count)} />
        <Stat label="Health Score" value={String(dashboard.health_score)} />
        <Stat label="Health Status" value={dashboard.health_status} />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <ExpenseCard title="Highest Expense" expense={dashboard.highest_expense} />
        <ExpenseCard title="Lowest Expense" expense={dashboard.lowest_expense} />
      </div>

      <div>
        <h2 className="mb-2 text-lg font-medium text-gray-900">Category Totals</h2>
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {Object.entries(dashboard.category_totals).map(([category, total]) => (
            <li key={category} className="flex justify-between px-3 py-2 text-sm">
              <span className="text-gray-700">{category}</span>
              <span className="font-medium text-gray-900">{formatCurrency(total)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-gray-200 p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  )
}

function ExpenseCard({
  title,
  expense,
}: {
  title: string
  expense: DashboardResponse['highest_expense']
}) {
  return (
    <div className="rounded border border-gray-200 p-3">
      <p className="text-xs text-gray-500">{title}</p>
      {expense ? (
        <p className="text-sm text-gray-900">
          {expense.name} ({expense.category}) — {formatCurrency(expense.amount)}
        </p>
      ) : (
        <p className="text-sm text-gray-400">N/A</p>
      )}
    </div>
  )
}
