import { useEffect, useState } from 'react'
import { createBill, deleteBill, listBills, payBill, unpayBill, updateBill } from '../api/bills'
import { BillForm } from '../components/bills/BillForm'
import type { BillFormValues } from '../components/bills/BillForm'
import type { BillResponse } from '../types/bills'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; bills: BillResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function BillsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingBill, setEditingBill] = useState<BillResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listBills()
      .then((bills) => setState({ status: 'success', bills }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listBills()
      .then((bills) => {
        if (!cancelled) setState({ status: 'success', bills })
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

  function handleSubmit(values: BillFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingBill ? updateBill(editingBill.id, values) : createBill(values)

    promise
      .then(() => {
        setEditingBill(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save bill')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(bill: BillResponse) {
    if (!window.confirm(`Delete "${bill.name}"?`)) return

    setMutationError(null)
    deleteBill(bill.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete bill')
      })
  }

  function handleTogglePaid(bill: BillResponse) {
    setMutationError(null)
    const promise = bill.is_paid ? unpayBill(bill.id) : payBill(bill.id)
    promise
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to update bill status')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading bills...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load bills: {state.message}</p>
  }

  const { bills } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Bills</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <BillForm
        key={editingBill?.id ?? 'create'}
        initial={editingBill}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingBill(null)}
      />

      {bills.length === 0 ? (
        <p className="text-sm text-gray-500">No bills yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {bills.map((bill) => (
            <li key={bill.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <span className="font-medium text-gray-900">{bill.name}</span>{' '}
                <span className="text-gray-500">(due day {bill.due_day})</span>{' '}
                {bill.is_paid ? (
                  <span className="text-green-600">Paid</span>
                ) : (
                  <span className="text-amber-600">Unpaid</span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(bill.amount)}</span>
                <button
                  type="button"
                  onClick={() => handleTogglePaid(bill)}
                  className="text-blue-600 hover:underline"
                >
                  {bill.is_paid ? 'Mark Unpaid' : 'Mark Paid'}
                </button>
                <button
                  type="button"
                  onClick={() => setEditingBill(bill)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(bill)}
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
