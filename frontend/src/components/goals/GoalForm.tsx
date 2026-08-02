import { useState } from 'react'
import type { FormEvent } from 'react'
import type { GoalResponse } from '../../types/goals'

export interface GoalFormValues {
  name: string
  target_amount: number
  current_amount: number
}

interface GoalFormProps {
  initial: GoalResponse | null
  submitting: boolean
  onSubmit: (values: GoalFormValues) => void
  onCancel: () => void
}

export function GoalForm({ initial, submitting, onSubmit, onCancel }: GoalFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [targetAmount, setTargetAmount] = useState(initial ? String(initial.target_amount) : '')
  const [currentAmount, setCurrentAmount] = useState(
    initial ? String(initial.current_amount) : '0',
  )
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setFormError('Name is required.')
      return
    }

    const parsedTarget = Number(targetAmount)
    if (!Number.isFinite(parsedTarget) || parsedTarget <= 0) {
      setFormError('Target amount must be greater than 0.')
      return
    }

    const parsedCurrent = Number(currentAmount)
    if (!Number.isFinite(parsedCurrent) || parsedCurrent < 0) {
      setFormError('Current amount must be 0 or greater.')
      return
    }

    setFormError(null)
    onSubmit({ name: name.trim(), target_amount: parsedTarget, current_amount: parsedCurrent })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="goal-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="goal-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="goal-target-amount" className="text-xs text-gray-500">
          Target Amount
        </label>
        <input
          id="goal-target-amount"
          type="number"
          step="0.01"
          min="0"
          value={targetAmount}
          onChange={(e) => setTargetAmount(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="goal-current-amount" className="text-xs text-gray-500">
          Current Amount
        </label>
        <input
          id="goal-current-amount"
          type="number"
          step="0.01"
          min="0"
          value={currentAmount}
          onChange={(e) => setCurrentAmount(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Goal'}
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
