import { useState } from 'react'
import type { FormEvent } from 'react'
import { EXPENSE_CATEGORIES } from '../../types/expenses'
import type { ExpenseCategory } from '../../types/expenses'
import { RECURRENCE_FREQUENCIES } from '../../types/recurringExpenses'
import type {
  RecurrenceFrequency,
  RecurringExpenseTemplateResponse,
} from '../../types/recurringExpenses'

export interface RecurringExpenseTemplateFormValues {
  name: string
  category: ExpenseCategory
  amount: number
  frequency: RecurrenceFrequency
  next_occurrence: string
  is_active: boolean
}

interface RecurringExpenseTemplateFormProps {
  initial: RecurringExpenseTemplateResponse | null
  submitting: boolean
  onSubmit: (values: RecurringExpenseTemplateFormValues) => void
  onCancel: () => void
}

export function RecurringExpenseTemplateForm({
  initial,
  submitting,
  onSubmit,
  onCancel,
}: RecurringExpenseTemplateFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [category, setCategory] = useState<ExpenseCategory>(initial?.category ?? EXPENSE_CATEGORIES[0])
  const [amount, setAmount] = useState(initial ? String(initial.amount) : '')
  const [frequency, setFrequency] = useState<RecurrenceFrequency>(initial?.frequency ?? 'MONTHLY')
  const [nextOccurrence, setNextOccurrence] = useState(initial?.next_occurrence ?? '')
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)
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

    if (!nextOccurrence) {
      setFormError('Next occurrence date is required.')
      return
    }

    setFormError(null)
    onSubmit({
      name: name.trim(),
      category,
      amount: parsedAmount,
      frequency,
      next_occurrence: nextOccurrence,
      is_active: isActive,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="recurring-expense-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="recurring-expense-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="recurring-expense-category" className="text-xs text-gray-500">
          Category
        </label>
        <select
          id="recurring-expense-category"
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
        <label htmlFor="recurring-expense-amount" className="text-xs text-gray-500">
          Amount
        </label>
        <input
          id="recurring-expense-amount"
          type="number"
          step="0.01"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="recurring-expense-frequency" className="text-xs text-gray-500">
          Frequency
        </label>
        <select
          id="recurring-expense-frequency"
          value={frequency}
          onChange={(e) => setFrequency(e.target.value as RecurrenceFrequency)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        >
          {RECURRENCE_FREQUENCIES.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="recurring-expense-next-occurrence" className="text-xs text-gray-500">
          Next Occurrence
        </label>
        <input
          id="recurring-expense-next-occurrence"
          type="date"
          value={nextOccurrence}
          onChange={(e) => setNextOccurrence(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
        Active
      </label>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Recurring Expense'}
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
