import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { createHousehold, listGuardianChildren, listMyHouseholds } from '../api/households'
import type { ChildSummaryResponse, HouseholdResponse } from '../types/households'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; households: HouseholdResponse[] }

export function HouseholdsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [children, setChildren] = useState<ChildSummaryResponse[]>([])
  const [name, setName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    listMyHouseholds()
      .then((households) => setState({ status: 'success', households }))
      .catch((err: unknown) => {
        setState({ status: 'error', message: err instanceof Error ? err.message : 'Unknown error' })
      })
  }

  useEffect(() => {
    let cancelled = false

    listMyHouseholds()
      .then((households) => {
        if (!cancelled) setState({ status: 'success', households })
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ status: 'error', message: err instanceof Error ? err.message : 'Unknown error' })
        }
      })

    listGuardianChildren()
      .then((result) => {
        if (!cancelled) setChildren(result)
      })
      .catch(() => {
        // Non-critical section of this page -- a failure here shouldn't
        // block the households list from rendering.
      })

    return () => {
      cancelled = true
    }
  }, [])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmedName = name.trim()

    if (!trimmedName) {
      setFormError('Household name is required.')
      return
    }

    setFormError(null)
    setSubmitting(true)
    createHousehold({ name: trimmedName })
      .then(() => {
        setName('')
        refetch()
      })
      .catch((err: unknown) => {
        setFormError(err instanceof Error ? err.message : 'Failed to create household')
      })
      .finally(() => setSubmitting(false))
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Households</h1>

      <form
        onSubmit={handleSubmit}
        className="flex items-end gap-3 rounded border border-gray-200 p-4"
      >
        <div className="flex flex-1 flex-col gap-1">
          <label htmlFor="household-name" className="text-xs text-gray-500">
            New household name
          </label>
          <input
            id="household-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {submitting ? 'Creating...' : 'Create Household'}
        </button>
      </form>
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      {state.status === 'loading' && <p className="text-sm text-gray-600">Loading households...</p>}
      {state.status === 'error' && (
        <p className="text-sm text-red-600">Failed to load households: {state.message}</p>
      )}
      {state.status === 'success' && (
        <div>
          <h2 className="text-sm font-medium text-gray-700">My Households</h2>
          {state.households.length === 0 ? (
            <p className="mt-2 text-sm text-gray-500">You don't belong to any households yet.</p>
          ) : (
            <ul className="mt-2 divide-y divide-gray-200 rounded border border-gray-200">
              {state.households.map((household) => (
                <li key={household.id} className="flex items-center justify-between px-3 py-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-900">{household.name}</span>{' '}
                    <span className="text-gray-500">
                      ({household.members.length}{' '}
                      {household.members.length === 1 ? 'member' : 'members'})
                    </span>
                  </div>
                  <Link to={`/households/${household.id}`} className="text-blue-600 hover:underline">
                    Manage
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div>
        <h2 className="text-sm font-medium text-gray-700">My Children</h2>
        {children.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">No linked children.</p>
        ) : (
          <ul className="mt-2 divide-y divide-gray-200 rounded border border-gray-200">
            {children.map(({ child, relationship }) => (
              <li key={relationship.id} className="px-3 py-2 text-sm">
                <span className="font-medium text-gray-900">{child.username}</span>{' '}
                <span className="text-gray-500">({child.email})</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
