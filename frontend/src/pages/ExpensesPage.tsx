import { useEffect, useState } from 'react'
import { createExpense, deleteExpense, listExpenses, updateExpense } from '../api/expenses'
import { apiGetBlob } from '../api/client'
import { downloadBlob } from '../utils/download'
import { ExpenseForm } from '../components/expenses/ExpenseForm'
import type { ExpenseFormValues } from '../components/expenses/ExpenseForm'
import type { ExpenseResponse } from '../types/expenses'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; expenses: ExpenseResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function ExpensesPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingExpense, setEditingExpense] = useState<ExpenseResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listExpenses()
      .then((expenses) => setState({ status: 'success', expenses }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listExpenses()
      .then((expenses) => {
        if (!cancelled) setState({ status: 'success', expenses })
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

  function handleSubmit(values: ExpenseFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingExpense
      ? updateExpense(editingExpense.id, values)
      : createExpense(values)

    promise
      .then(() => {
        setEditingExpense(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save expense')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(expense: ExpenseResponse) {
    if (!window.confirm(`Delete "${expense.name}"?`)) return

    setMutationError(null)
    deleteExpense(expense.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete expense')
      })
  }

  function handleExportCsv() {
    setMutationError(null)
    apiGetBlob('/expenses/export')
      .then((blob) => downloadBlob(blob, 'expenses.csv'))
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to export expenses')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading expenses...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load expenses: {state.message}</p>
  }

  const { expenses } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Expenses</h1>

      <button
        type="button"
        onClick={handleExportCsv}
        className="text-sm text-blue-600 hover:underline"
      >
        Download CSV
      </button>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <ExpenseForm
        key={editingExpense?.id ?? 'create'}
        initial={editingExpense}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingExpense(null)}
      />

      {expenses.length === 0 ? (
        <p className="text-sm text-gray-500">No expenses yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {expenses.map((expense) => (
            <li key={expense.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <span className="font-medium text-gray-900">{expense.name}</span>{' '}
                <span className="text-gray-500">({expense.category})</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(expense.amount)}</span>
                <button
                  type="button"
                  onClick={() => setEditingExpense(expense)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(expense)}
                  className="text-red-600 hover:underline"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
