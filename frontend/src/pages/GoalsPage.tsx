import { useEffect, useState } from 'react'
import {
  adjustGoalBalance,
  contributeToGoal,
  createGoal,
  deleteGoal,
  getGoalLedgerEntries,
  listGoals,
  reconcileGoal,
  reverseGoalLedgerEntry,
  updateGoal,
  withdrawFromGoal,
} from '../api/goals'
import { GoalForm } from '../components/goals/GoalForm'
import type { GoalFormValues } from '../components/goals/GoalForm'
import type { GoalLedgerEntryResponse, GoalReconcileResponse, GoalResponse } from '../types/goals'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; goals: GoalResponse[] }

type LedgerState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; entries: GoalLedgerEntryResponse[]; reconcile: GoalReconcileResponse }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function GoalsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingGoal, setEditingGoal] = useState<GoalResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  const [expandedGoalId, setExpandedGoalId] = useState<number | null>(null)
  const [ledgerState, setLedgerState] = useState<LedgerState>({ status: 'loading' })
  const [ledgerAmount, setLedgerAmount] = useState('')

  function refetch() {
    setState({ status: 'loading' })
    listGoals()
      .then((goals) => setState({ status: 'success', goals }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listGoals()
      .then((goals) => {
        if (!cancelled) setState({ status: 'success', goals })
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

  function refetchLedger(goalId: number) {
    setLedgerState({ status: 'loading' })
    Promise.all([getGoalLedgerEntries(goalId), reconcileGoal(goalId)])
      .then(([entries, reconcile]) => setLedgerState({ status: 'success', entries, reconcile }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setLedgerState({ status: 'error', message })
      })
  }

  function handleToggleLedger(goal: GoalResponse) {
    if (expandedGoalId === goal.id) {
      setExpandedGoalId(null)
      return
    }
    setExpandedGoalId(goal.id)
    setLedgerAmount('')
    refetchLedger(goal.id)
  }

  function handleSubmit(values: GoalFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingGoal ? updateGoal(editingGoal.id, values) : createGoal(values)

    promise
      .then(() => {
        setEditingGoal(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save goal')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(goal: GoalResponse) {
    if (!window.confirm(`Delete "${goal.name}"?`)) return

    setMutationError(null)
    deleteGoal(goal.id)
      .then(() => {
        if (expandedGoalId === goal.id) setExpandedGoalId(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete goal')
      })
  }

  function handleLedgerAction(
    goalId: number,
    action: (id: number, request: { amount: number }) => Promise<GoalResponse>,
  ) {
    const amount = Number(ledgerAmount)
    if (!Number.isFinite(amount)) {
      setMutationError('Amount must be a valid number.')
      return
    }

    setMutationError(null)
    action(goalId, { amount })
      .then(() => {
        setLedgerAmount('')
        refetch()
        refetchLedger(goalId)
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to update goal balance')
      })
  }

  function handleReverse(goalId: number, entryId: string) {
    if (!window.confirm('Reverse this ledger entry?')) return

    setMutationError(null)
    reverseGoalLedgerEntry(goalId, { entry_id: entryId })
      .then(() => {
        refetch()
        refetchLedger(goalId)
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to reverse entry')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading goals...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load goals: {state.message}</p>
  }

  const { goals } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Goals</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <GoalForm
        key={editingGoal?.id ?? 'create'}
        initial={editingGoal}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingGoal(null)}
      />

      {goals.length === 0 ? (
        <p className="text-sm text-gray-500">No goals yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {goals.map((goal) => {
            const progressPercent = Math.min(
              100,
              (goal.current_amount / goal.target_amount) * 100,
            )
            return (
              <li key={goal.id} className="p-3 text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900">{goal.name}</span>{' '}
                    <span className="text-gray-500">
                      {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
                    </span>
                    <div className="mt-1 h-2 w-full max-w-xs rounded bg-gray-200">
                      <div
                        className="h-2 rounded bg-blue-600"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleToggleLedger(goal)}
                      className="text-blue-600 hover:underline"
                    >
                      {expandedGoalId === goal.id ? 'Hide Ledger' : 'View Ledger'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingGoal(goal)}
                      className="text-blue-600 hover:underline"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(goal)}
                      className="text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {expandedGoalId === goal.id && (
                  <div className="mt-3 space-y-3 rounded border border-gray-200 bg-gray-50 p-3">
                    {ledgerState.status === 'loading' && (
                      <p className="text-gray-500">Loading ledger...</p>
                    )}
                    {ledgerState.status === 'error' && (
                      <p className="text-red-600">Failed to load ledger: {ledgerState.message}</p>
                    )}
                    {ledgerState.status === 'success' && (
                      <>
                        {ledgerState.reconcile.is_reconciled ? (
                          <p className="text-green-700">Reconciled</p>
                        ) : (
                          <p className="text-red-600">
                            Out of sync — ledger balance is{' '}
                            {formatCurrency(ledgerState.reconcile.ledger_balance)}
                          </p>
                        )}

                        <div className="flex items-center gap-2">
                          <input
                            type="number"
                            step="0.01"
                            placeholder="Amount"
                            value={ledgerAmount}
                            onChange={(e) => setLedgerAmount(e.target.value)}
                            className="w-28 rounded border border-gray-300 px-2 py-1 text-sm"
                          />
                          <button
                            type="button"
                            onClick={() => handleLedgerAction(goal.id, contributeToGoal)}
                            className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white"
                          >
                            Contribute
                          </button>
                          <button
                            type="button"
                            onClick={() => handleLedgerAction(goal.id, withdrawFromGoal)}
                            className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white"
                          >
                            Withdraw
                          </button>
                          <button
                            type="button"
                            onClick={() => handleLedgerAction(goal.id, adjustGoalBalance)}
                            className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white"
                          >
                            Adjust
                          </button>
                        </div>

                        {ledgerState.entries.length === 0 ? (
                          <p className="text-gray-500">No ledger entries yet.</p>
                        ) : (
                          <table className="w-full text-left text-xs">
                            <thead className="text-gray-500">
                              <tr>
                                <th className="pb-1">Type</th>
                                <th className="pb-1">Amount</th>
                                <th className="pb-1">Date</th>
                                <th className="pb-1">Note</th>
                                <th className="pb-1"></th>
                              </tr>
                            </thead>
                            <tbody>
                              {ledgerState.entries.map((entry) => (
                                <tr key={entry.entry_id} className="border-t border-gray-200">
                                  <td className="py-1">{entry.entry_type}</td>
                                  <td className="py-1">{formatCurrency(entry.amount)}</td>
                                  <td className="py-1">{entry.effective_date}</td>
                                  <td className="py-1">{entry.note}</td>
                                  <td className="py-1 text-right">
                                    {entry.entry_type !== 'REVERSAL' && (
                                      <button
                                        type="button"
                                        onClick={() => handleReverse(goal.id, entry.entry_id)}
                                        className="text-red-600 hover:underline"
                                      >
                                        Reverse
                                      </button>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </>
                    )}
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
