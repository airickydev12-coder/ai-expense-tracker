import { useEffect, useState } from 'react'
import { assignUserRole, listUsers, revokeUserSessions, setUserActive } from '../api/admin'
import { useAuth } from '../context/AuthContext'
import { useStepUpAuth } from '../context/StepUpAuthContext'
import type { PlatformRole, UserResponse } from '../types/auth'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; users: UserResponse[] }

const ROLE_OPTIONS: PlatformRole[] = ['user', 'admin', 'super_admin']

const ROLE_LABELS: Record<PlatformRole, string> = {
  user: 'User',
  admin: 'Admin',
  super_admin: 'Super Admin',
}

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const { runWithStepUp } = useStepUpAuth()
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [search, setSearch] = useState('')
  const [actionError, setActionError] = useState<string | null>(null)
  const [actioningId, setActioningId] = useState<number | null>(null)

  const canAssignRoles = currentUser?.role === 'super_admin'

  useEffect(() => {
    let cancelled = false

    listUsers()
      .then((users) => {
        if (!cancelled) setState({ status: 'success', users })
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

  function refetch() {
    setState({ status: 'loading' })
    listUsers()
      .then((users) => setState({ status: 'success', users }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  function handleToggleActive(user: UserResponse) {
    const nextActive = !user.is_active
    if (
      !nextActive &&
      !window.confirm(`Deactivate ${user.username}? This ends all of their active sessions.`)
    ) {
      return
    }

    setActionError(null)
    setActioningId(user.id)
    runWithStepUp(() => setUserActive(user.id, { is_active: nextActive }))
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to update account status')
      })
      .finally(() => setActioningId(null))
  }

  function handleRoleChange(user: UserResponse, role: PlatformRole) {
    if (role === user.role) return

    setActionError(null)
    setActioningId(user.id)
    runWithStepUp(() => assignUserRole(user.id, { role }))
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to assign role')
      })
      .finally(() => setActioningId(null))
  }

  function handleRevokeSessions(user: UserResponse) {
    if (!window.confirm(`Revoke all sessions for ${user.username}? They will be signed out everywhere.`)) {
      return
    }

    setActionError(null)
    setActioningId(user.id)
    revokeUserSessions(user.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to revoke sessions')
      })
      .finally(() => setActioningId(null))
  }

  return (
    <div className="space-y-4">
      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      <label className="flex flex-col gap-1 text-xs text-gray-500">
        Search
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by username or email"
          className="w-full max-w-xs rounded border border-gray-300 px-2 py-1 text-sm text-gray-900"
        />
      </label>

      {state.status === 'loading' && <p className="text-sm text-gray-600">Loading users...</p>}

      {state.status === 'error' && (
        <p className="text-sm text-red-600">Failed to load users: {state.message}</p>
      )}

      {state.status === 'success' && (
        <UserTable
          users={state.users.filter((user) => {
            const query = search.trim().toLowerCase()
            if (!query) return true
            return (
              user.username.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)
            )
          })}
          currentUserId={currentUser?.id ?? null}
          canAssignRoles={canAssignRoles}
          actioningId={actioningId}
          onToggleActive={handleToggleActive}
          onRoleChange={handleRoleChange}
          onRevokeSessions={handleRevokeSessions}
        />
      )}
    </div>
  )
}

function UserTable({
  users,
  currentUserId,
  canAssignRoles,
  actioningId,
  onToggleActive,
  onRoleChange,
  onRevokeSessions,
}: {
  users: UserResponse[]
  currentUserId: number | null
  canAssignRoles: boolean
  actioningId: number | null
  onToggleActive: (user: UserResponse) => void
  onRoleChange: (user: UserResponse, role: PlatformRole) => void
  onRevokeSessions: (user: UserResponse) => void
}) {
  if (users.length === 0) {
    return <p className="text-sm text-gray-500">No users match.</p>
  }

  return (
    <ul className="divide-y divide-gray-200 rounded border border-gray-200">
      {users.map((user) => {
        const isSelf = user.id === currentUserId
        const busy = actioningId === user.id

        return (
          <li key={user.id} className="flex flex-wrap items-center gap-3 px-3 py-3 text-sm">
            <div className="min-w-40 flex-1">
              <p className="font-medium text-gray-900">
                {user.username} {isSelf && <span className="text-xs text-gray-400">(you)</span>}
              </p>
              <p className="text-xs text-gray-500">{user.email}</p>
            </div>

            <StatusBadge isActive={user.is_active} />

            {canAssignRoles ? (
              <select
                aria-label={`Role for ${user.username}`}
                value={user.role}
                disabled={isSelf || busy}
                onChange={(e) => onRoleChange(user, e.target.value as PlatformRole)}
                className="rounded border border-gray-300 px-2 py-1 text-xs text-gray-900 disabled:opacity-50"
              >
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>
                    {ROLE_LABELS[role]}
                  </option>
                ))}
              </select>
            ) : (
              <span className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">
                {ROLE_LABELS[user.role]}
              </span>
            )}

            <div className="ml-auto flex items-center gap-3">
              <button
                type="button"
                disabled={isSelf || busy}
                onClick={() => onToggleActive(user)}
                className="text-blue-600 hover:underline disabled:opacity-50"
              >
                {user.is_active ? 'Deactivate' : 'Activate'}
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => onRevokeSessions(user)}
                className="text-red-600 hover:underline disabled:opacity-50"
              >
                Revoke Sessions
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  const className = isActive ? 'bg-green-100 text-green-800' : 'bg-gray-200 text-gray-600'
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${className}`}>
      {isActive ? 'Active' : 'Inactive'}
    </span>
  )
}
