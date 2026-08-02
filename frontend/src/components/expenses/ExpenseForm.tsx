import { useState } from 'react'
import type { FormEvent } from 'react'
import { EXPENSE_CATEGORIES } from '../../types/expenses'
import type { ExpenseCategory, ExpenseResponse } from '../../types/expenses'

export interface ExpenseFormValues {
  name: string
  category: ExpenseCategory
  amount: number
}

interface ExpenseFormProps {
  initial: ExpenseResponse | null
  submitting: boolean
  onSubmit: (values: ExpenseFormValues) => void
  onCancel: () => void
}

export function ExpenseForm({ initial, submitting, onSubmit, onCancel }: ExpenseFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [category, setCategory] = useState<ExpenseCategory>(initial?.category ?? EXPENSE_CATEGORIES[0])
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '')
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

    setFormError(null)
    onSubmit({ name: name.trim(), category, amount: parsedAmount })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="expense-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="expense-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="expense-category" className="text-xs text-gray-500">
          Category
        </label>
        <select
          id="expense-category"
          value={category}
          onChange={(e) => setCategory(e.target.value as ExpenseCategory)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {EXPENSE_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="expense-amount" className="text-xs text-gray-500">
          Amount
        </label>
        <input
          id="expense-amount"
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
          {initial ? 'Save Changes' : 'Add Expense'}
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
