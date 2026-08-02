import { useState } from 'react'
import type { FormEvent } from 'react'
import type { AccountResponse } from '../../types/accounts'

export interface AccountFormValues {
  name: string
  account_type: string
  balance: number
}

interface AccountFormProps {
  initial: AccountResponse | null
  submitting: boolean
  onSubmit: (values: AccountFormValues) => void
  onCancel: () => void
}

export function AccountForm({ initial, submitting, onSubmit, onCancel }: AccountFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [accountType, setAccountType] = useState(initial?.account_type ?? '')
  const [balance, setBalance] = useState(initial ? String(initial.balance) : '')
  const [formError, setFormError] = useState<string | null>(null)

  function handleSubmit(e: FormEvent) {
    e.preventDefault()

    if (!name.trim()) {
      setFormError('Name is required.')
      return
    }
    if (!accountType.trim()) {
      setFormError('Account type is required.')
      return
    }

    const parsedBalance = Number(balance)
    if (!Number.isFinite(parsedBalance)) {
      setFormError('Balance must be a number.')
      return
    }

    setFormError(null)
    onSubmit({ name: name.trim(), account_type: accountType.trim(), balance: parsedBalance })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 rounded border border-gray-200 p-4">
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <div className="flex flex-col gap-1">
        <label htmlFor="account-name" className="text-xs text-gray-500">
          Name
        </label>
        <input
          id="account-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="account-type" className="text-xs text-gray-500">
          Account Type
        </label>
        <input
          id="account-type"
          type="text"
          value={accountType}
          onChange={(e) => setAccountType(e.target.value)}
          placeholder="e.g. Bank, Cash, Credit Card"
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="account-balance" className="text-xs text-gray-500">
          Balance
        </label>
        <input
          id="account-balance"
          type="number"
          step="0.01"
          value={balance}
          onChange={(e) => setBalance(e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm"
        />
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {initial ? 'Save Changes' : 'Add Account'}
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
