import { useEffect, useState } from 'react'
import { getAdminOverview, listUsers } from '../api/admin'
import type { AdminOverviewResponse } from '../types/admin'
import type { UserResponse } from '../types/auth'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; overview: AdminOverviewResponse; users: UserResponse[] }

const DAY_MS = 24 * 60 * 60 * 1000

function countRegisteredSince(users: UserResponse[], days: number): number {
  const cutoff = Date.now() - days * DAY_MS
  return users.filter((user) => new Date(user.created_at).getTime() >= cutoff).length
}

export function AdminOverviewPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false

    Promise.all([getAdminOverview(), listUsers()])
      .then(([overview, users]) => {
        if (!cancelled) setState({ status: 'success', overview, users })
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

  if (state.status === 'loading') {
    return <p className="text-sm text-gray-600">Loading overview...</p>
  }

  if (state.status === 'error') {
    return <p className="text-sm text-red-600">Failed to load admin overview: {state.message}</p>
  }

  const { overview, users } = state
  const activeCount = users.filter((user) => user.is_active).length
  const adminCount = users.filter((user) => user.role !== 'user').length

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500">
        Signed in as <span className="font-medium text-gray-900">{overview.admin_username}</span>{' '}
        ({overview.admin_role})
      </p>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Total Users" value={String(users.length)} />
        <Stat label="Active" value={String(activeCount)} />
        <Stat label="Inactive" value={String(users.length - activeCount)} />
        <Stat label="Admins" value={String(adminCount)} />
        <Stat label="New (7 days)" value={String(countRegisteredSince(users, 7))} />
        <Stat label="New (30 days)" value={String(countRegisteredSince(users, 30))} />
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border border-gray-200 p-3">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  )
}
