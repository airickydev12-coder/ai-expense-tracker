import { useEffect, useState } from 'react'
import { checkNotificationsNow, getNotificationLog } from '../api/notifications'
import type { NotificationLogEntryResponse } from '../types/notifications'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'success'; entries: NotificationLogEntryResponse[] }

function statusClass(status: string): string {
  return status === 'SENT' ? 'text-green-600' : 'text-red-600'
}

export function NotificationsPage() {
  const [state, setState] = useState<LoadState>({ status: 'loading' })
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState<string | null>(null)
  const [checkMessage, setCheckMessage] = useState<string | null>(null)

  function refetch() {
    setState({ status: 'loading' })
    getNotificationLog()
      .then((entries) => setState({ status: 'success', entries }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState({ status: 'error', message })
      })
  }

  useEffect(() => {
    let cancelled = false

    getNotificationLog()
      .then((entries) => {
        if (!cancelled) setState({ status: 'success', entries })
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

  function handleCheckNow() {
    setChecking(true)
    setCheckError(null)
    setCheckMessage(null)
    checkNotificationsNow()
      .then((result) => {
        setCheckMessage(
          result.new_entry_count === 0
            ? 'No new notifications right now.'
            : `${result.new_entry_count} new notification(s).`,
        )
        refetch()
      })
      .catch((err: unknown) => {
        setCheckError(err instanceof Error ? err.message : 'Failed to check notifications')
      })
      .finally(() => setChecking(false))
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4">
      <h1 className="text-2xl font-semibold text-gray-900">Notifications</h1>

      {checkError && <p className="text-sm text-red-600">{checkError}</p>}
      {checkMessage && <p className="text-sm text-green-600">{checkMessage}</p>}

      <button
        type="button"
        onClick={handleCheckNow}
        disabled={checking}
        className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {checking ? 'Checking...' : 'Check Now'}
      </button>

      {state.status === 'loading' && <p className="text-sm text-gray-600">Loading notifications...</p>}

      {state.status === 'error' && (
        <p className="text-sm text-red-600">Failed to load notifications: {state.message}</p>
      )}

      {state.status === 'success' && (
        <>
          {state.entries.length === 0 ? (
            <p className="text-sm text-gray-500">No notifications logged yet.</p>
          ) : (
            <ul className="divide-y divide-gray-200 rounded border border-gray-200">
              {state.entries.map((entry) => (
                <li key={entry.id} className="space-y-1 px-3 py-2 text-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`font-medium ${statusClass(entry.status)}`}>{entry.status}</span>
                    <span className="text-gray-500">{new Date(entry.sent_at).toLocaleString()}</span>
                  </div>
                  <p className="font-medium text-gray-900">{entry.subject}</p>
                  <p className="whitespace-pre-line text-gray-700">{entry.body}</p>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}
