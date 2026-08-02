import { useEffect, useState } from 'react'
import { createAccount, deleteAccount, listAccounts, updateAccount } from '../api/accounts'
import { AccountForm } from '../components/accounts/AccountForm'
import type { AccountFormValues } from '../components/accounts/AccountForm'
import type { AccountResponse } from '../types/accounts'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; accounts: AccountResponse[] }

function formatCurrency(value: number): string {
  return `$${value.toFixed(2)}`
}

export function AccountsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [editingAccount, setEditingAccount] = useState<AccountResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listAccounts()
      .then((accounts) => setState({ status: 'success', accounts }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    listAccounts()
      .then((accounts) => {
        if (!cancelled) setState({ status: 'success', accounts })
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

  function handleSubmit(values: AccountFormValues) {
    setSubmitting(true)
    setMutationError(null)

    const promise = editingAccount
      ? updateAccount(editingAccount.id, values)
      : createAccount(values)

    promise
      .then(() => {
        setEditingAccount(null)
        refetch()
      })
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to save account')
      })
      .finally(() => setSubmitting(false))
  }

  function handleDelete(account: AccountResponse) {
    if (!window.confirm(`Delete "${account.name}"?`)) return

    setMutationError(null)
    deleteAccount(account.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setMutationError(err instanceof Error ? err.message : 'Failed to delete account')
      })
  }

  if (state.status === 'loading') {
    return <p className="p-4 text-gray-600">Loading accounts...</p>
  }

  if (state.status === 'error') {
    return <p className="p-4 text-red-600">Failed to load accounts: {state.message}</p>
  }

  const { accounts } = state

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Accounts</h1>

      {mutationError && <p className="text-sm text-red-600">{mutationError}</p>}

      <AccountForm
        key={editingAccount?.id ?? 'create'}
        initial={editingAccount}
        submitting={submitting}
        onSubmit={handleSubmit}
        onCancel={() => setEditingAccount(null)}
      />

      {accounts.length === 0 ? (
        <p className="text-sm text-gray-500">No accounts yet.</p>
      ) : (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {accounts.map((account) => (
            <li key={account.id} className="flex items-center justify-between px-3 py-2 text-sm">
              <div>
                <span className="font-medium text-gray-900">{account.name}</span>{' '}
                <span className="text-gray-500">({account.account_type})</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="font-medium text-gray-900">{formatCurrency(account.balance)}</span>
                <button
                  type="button"
                  onClick={() => setEditingAccount(account)}
                  className="text-blue-600 hover:underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(account)}
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
