import { useState } from 'react'
import type { FormEvent } from 'react'
import type { DebtResponse } from '../../types/debt'

export interface DebtFormValues {
  name: string
  balance: number
  interest_rate: number
  minimum_payment: number
}

interface DebtFormProps {
  initial: DebtResponse | null
  submitting: boolean
  onSubmit: (values: DebtFormValues) => void
  onCancel: () => void
}

export function DebtForm({ initial, submitting, onSubmit, onCancel }: DebtFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [balance, setBalance] = useState(initial ? String(initial.balance) : '')
  const [interestRate, setInterestRate] = useState(initial ? String(initial.interest_rate) : '')
  const [minimumPayment, setMinimumPayment] = useState(
    initial ? String(initial.minimum_payment) : '',
  )
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setFormError('Name is required.')
      return
    }

    const parsedBalance = Number(balance)
    if (!Number.isFinite(parsedBalance) || parsedBalance < 0) {
      setFormError('Balance must be a number that is 0 or greater.')
      return
    }

    const parsedInterestRate = Number(interestRate)
    if (!Number.isFinite(parsedInterestRate) || parsedInterestRate < 0) {
      setFormError('Interest rate must be a number that is 0 or greater.')
      return
    }

    const parsedMinimumPayment = Number(minimumPayment)
    if (!Number.isFinite(parsedMinimumPayment) || parsedMinimumPayment < 0) {
      setFormError('Minimum payment must be a number that is 0 or greater.')
      return
    }

    setFormError(null)
    onSubmit({
      name: name.trim(),
      balance: parsedBalance,
      interest_rate: parsedInterestRate,
      minimum_payment: parsedMinimumPayment,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="debt-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="debt-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="debt-balance" className="text-xs text-gray-500">
          Balance
        </label>
        <input
          id="debt-balance"
          type="number"
          step="0.01"
          min="0"
          value={balance}
          onChange={(e) => setBalance(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="debt-interest-rate" className="text-xs text-gray-500">
          Interest Rate (%)
        </label>
        <input
          id="debt-interest-rate"
          type="number"
          step="0.01"
          min="0"
          value={interestRate}
          onChange={(e) => setInterestRate(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="debt-minimum-payment" className="text-xs text-gray-500">
          Minimum Payment
        </label>
        <input
          id="debt-minimum-payment"
          type="number"
          step="0.01"
          min="0"
          value={minimumPayment}
          onChange={(e) => setMinimumPayment(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Debt'}
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
