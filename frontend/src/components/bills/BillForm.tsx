import { useState } from 'react'
import type { FormEvent } from 'react'
import type { BillResponse } from '../../types/bills'

export interface BillFormValues {
  name: string
  amount: number
  due_day: number
  is_paid: boolean
}

interface BillFormProps {
  initial: BillResponse | null
  submitting: boolean
  onSubmit: (values: BillFormValues) => void
  onCancel: () => void
}

export function BillForm({ initial, submitting, onSubmit, onCancel }: BillFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '')
  const [dueDay, setDueDay] = useState(initial ? String(initial.due_day) : '1')
  const [isPaid, setIsPaid] = useState(initial?.is_paid ?? false)
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setFormError('Name is required.')
      return
    }

    const parsedAmount = Number(amount)
    if (!Number.isFinite(parsedAmount) || parsedAmount < 0) {
      setFormError('Amount must be a number that is 0 or greater.')
      return
    }

    const parsedDueDay = Number(dueDay)
    if (!Number.isInteger(parsedDueDay) || parsedDueDay < 1 || parsedDueDay > 31) {
      setFormError('Due day must be a whole number between 1 and 31.')
      return
    }

    setFormError(null)
    onSubmit({
      name: name.trim(),
      amount: parsedAmount,
      due_day: parsedDueDay,
      is_paid: isPaid,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="bill-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="bill-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="bill-amount" className="text-xs text-gray-500">
          Amount
        </label>
        <input
          id="bill-amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="bill-due-day" className="text-xs text-gray-500">
          Due Day (1-31)
        </label>
        <input
          id="bill-due-day"
          type="number"
          min="1"
          max="31"
          step="1"
          value={dueDay}
          onChange={(e) => setDueDay(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input type="checkbox" checked={isPaid} onChange={(e) => setIsPaid(e.target.checked)} />
        Paid
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Bill'}
        </button>
        {initial && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
