import { useEffect, useState } from 'react'
import { applyDebtPayment, createDebt, deleteDebt, listDebts, updateDebt } from '../api/debt'
import { DebtForm } from '../components/debt/DebtForm'
import type { DebtFormValues } from '../components/debt/DebtForm'
import type { DebtResponse } from '../types/debt'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; debts: DebtResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function DebtPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingDebt, setEditingDebt] = useState<DebtResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listDebts()
      .then((debts) => setState({ status: 'success', debts }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listDebts()
      .then((debts) => {
        if (!cancelled) setState({ status: 'success', debts })
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

  function handleSubmit(values: DebtFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingDebt ? updateDebt(editingDebt.id, values) : createDebt(values)

    promise
      .then(() => {
        setEditingDebt(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save debt')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(debt: DebtResponse) {
    if (!window.confirm(`Delete "${debt.name}"?`)) return

    setMutationError(null)
    deleteDebt(debt.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete debt')
      })
  }

  function handleApplyPayment(debt: DebtResponse) {
    const input = window.prompt(`Payment amount for "${debt.name}"?`)
    if (input === null) return

    const payment = Number(input)
    if (!Number.isFinite(payment)) {
      setMutationError('Payment must be a valid number.')
      return
    }

    setMutationError(null)
    applyDebtPayment(debt.id, payment)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to apply payment')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading debts...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load debts: {state.message}</p>
  }

  const { debts } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Debt</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <DebtForm
        key={editingDebt?.id ?? 'create'}
        initial={editingDebt}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingDebt(null)}
      />

      {debts.length === 0 ? (
        <p className="text-sm text-gray-500">No debts yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {debts.map((debt) => (
            <li key={debt.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <span className="font-medium text-gray-900">{debt.name}</span>{' '}
                <span className="text-gray-500">
                  ({debt.interest_rate}% APR, min {formatCurrency(debt.minimum_payment)})
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(debt.balance)}</span>
                <button
                  type="button"
                  onClick={() => handleApplyPayment(debt)}
                  className="text-blue-600 hover:underline"
                >
                  Apply Payment
                </button>
                <button
                  type="button"
                  onClick={() => setEditingDebt(debt)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(debt)}
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
