import { useState } from 'react'
import type { FormEvent } from 'react'
import type { IncomeResponse } from '../../types/income'

export interface IncomeFormValues {
  source: string
  amount: number
}

interface IncomeFormProps {
  initial: IncomeResponse | null
  submitting: boolean
  onSubmit: (values: IncomeFormValues) => void
  onCancel: () => void
}

export function IncomeForm({ initial, submitting, onSubmit, onCancel }: IncomeFormProps) {
  const [source, setSource] = useState(initial?.source ?? '')
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '')
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!source.trim()) {
      setFormError('Source is required.')
      return
    }

    const parsedAmount = Number(amount)
    if (!Number.isFinite(parsedAmount) || parsedAmount < 0) {
      setFormError('Amount must be a number that is 0 or greater.')
      return
    }

    setFormError(null)
    onSubmit({ source: source.trim(), amount: parsedAmount })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="income-source" className="text-xs text-gray-500">
          Source
        </label>
        <input
          id="income-source"
          type="text"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="income-amount" className="text-xs text-gray-500">
          Amount
        </label>
        <input
          id="income-amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Income'}
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
