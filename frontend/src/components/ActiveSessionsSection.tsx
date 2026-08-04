import { useEffect, useState } from 'react'
import { listSessions, revokeAllSessions, revokeSession } from '../api/auth'
import { useStepUpAuth } from '../context/StepUpAuthContext'
import type { SessionResponse } from '../types/auth'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; sessions: SessionResponse[] }

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

export function ActiveSessionsSection() {
  const { runWithStepUp } = useStepUpAuth()
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [actionError, setActionError] = useState<string | null>(null)
  const [actioningId, setActioningId] = useState<number | 'all' | null>(null)

  useEffect(() => {
    let cancelled = false

    listSessions()
      .then((sessions) => {
        if (!cancelled) setState({ status: 'success', sessions })
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
    listSessions()
      .then((sessions) => setState({ status: 'success', sessions }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  function handleRevoke(session: SessionResponse) {
    if (!window.confirm('Revoke this session? That device will be signed out.')) return

    setActionError(null)
    setActioningId(session.id)
    revokeSession(session.id)
      .then(() => refetch())
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to revoke session')
      })
      .finally(() => setActioningId(null))
  }

  function handleRevokeAll() {
    if (!window.confirm('Log out of every device, including this one?')) return

    setActionError(null)
    setActioningId('all')
    runWithStepUp(() => revokeAllSessions())
      .then(() => {
        // Full reload so the in-memory access token and AuthContext state
        // both reset cleanly -- the now-cookieless bootstrap lands on
        // /login on its own, same as a normal logout.
        window.location.href = '/login'
      })
      .catch((err: unknown) => {
        setActionError(err instanceof Error ? err.message : 'Failed to log out of all devices')
        setActioningId(null)
      })
  }

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-gray-900">Active Sessions</h2>
        {state.status === 'success' && state.sessions.length > 0 && (
          <button
            type="button"
            onClick={handleRevokeAll}
            disabled={actioningId === 'all'}
            className="text-sm text-red-600 hover:underline disabled:opacity-50"
          >
            Log out of all devices
          </button>
        )}
      </div>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      {state.status === 'loading' && <p className="text-sm text-gray-600">Loading sessions...</p>}
      {state.status === 'error' && (
        <p className="text-sm text-red-600">Failed to load sessions: {state.message}</p>
      )}

      {state.status === 'success' && (
        <ul className="divide-y divide-gray-200 rounded border border-gray-200">
          {state.sessions.map((session) => (
            <li key={session.id} className="flex flex-wrap items-center gap-3 px-3 py-3 text-sm">
              <div className="min-w-40 flex-1">
                <p className="text-gray-900">
                  {session.user_agent ?? 'Unknown device'}{' '}
                  {session.is_current && (
                    <span className="text-xs text-gray-400">(this device)</span>
                  )}
                </p>
                <p className="text-xs text-gray-500">
                  {session.ip_address ?? 'Unknown location'} — signed in{' '}
                  {formatDate(session.issued_at)}
                </p>
              </div>
              <button
                type="button"
                disabled={session.is_current || actioningId === session.id}
                onClick={() => handleRevoke(session)}
                className="text-red-600 hover:underline disabled:opacity-50"
              >
                Revoke
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
