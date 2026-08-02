import { useEffect, useState } from 'react'
import { createIncome, deleteIncome, listIncome, updateIncome } from '../api/income'
import { IncomeForm } from '../components/income/IncomeForm'
import type { IncomeFormValues } from '../components/income/IncomeForm'
import type { IncomeResponse } from '../types/income'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; income: IncomeResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function IncomePage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingIncome, setEditingIncome] = useState<IncomeResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listIncome()
      .then((income) => setState({ status: 'success', income }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listIncome()
      .then((income) => {
        if (!cancelled) setState({ status: 'success', income })
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

  function handleSubmit(values: IncomeFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingIncome
      ? updateIncome(editingIncome.id, values)
      : createIncome(values)

    promise
      .then(() => {
        setEditingIncome(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save income')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(entry: IncomeResponse) {
    if (!window.confirm(`Delete "${entry.source}"?`)) return

    setMutationError(null)
    deleteIncome(entry.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete income')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading income...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load income: {state.message}</p>
  }

  const { income } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Income</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <IncomeForm
        key={editingIncome?.id ?? 'create'}
        initial={editingIncome}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingIncome(null)}
      />

      {income.length === 0 ? (
        <p className="text-sm text-gray-500">No income entries yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {income.map((entry) => (
            <li key={entry.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <span className="font-medium text-gray-900">{entry.source}</span>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(entry.amount)}</span>
                <button
                  type="button"
                  onClick={() => setEditingIncome(entry)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(entry)}
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
